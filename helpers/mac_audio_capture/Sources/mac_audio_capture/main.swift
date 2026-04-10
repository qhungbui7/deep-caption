import AVFoundation
import CoreMedia
import Darwin
import Foundation
import ScreenCaptureKit

struct ControlMessage: Decodable {
    let action: String
    let source_id: String?
}

struct AudioHeader: Encodable {
    let sample_rate: Int
    let t0_ms: Int64
    let t1_ms: Int64
    let source_id: String
}

final class PacketWriter {
    private let fd: Int32
    private let lock = NSLock()

    init(fd: Int32) {
        self.fd = fd
    }

    func send(samples: [Float], sampleRate: Int, t0Ms: Int64, t1Ms: Int64, sourceID: String) {
        let header = AudioHeader(
            sample_rate: sampleRate,
            t0_ms: t0Ms,
            t1_ms: t1Ms,
            source_id: sourceID
        )
        guard let headerData = try? JSONEncoder().encode(header) else {
            return
        }
        var payload = Data()
        var headerLen = UInt32(headerData.count).bigEndian
        withUnsafeBytes(of: &headerLen) { payload.append(contentsOf: $0) }
        payload.append(headerData)
        samples.withUnsafeBufferPointer { ptr in
            let raw = UnsafeRawBufferPointer(ptr)
            payload.append(raw.bindMemory(to: UInt8.self))
        }

        var packet = Data()
        var packetLen = UInt32(payload.count).bigEndian
        withUnsafeBytes(of: &packetLen) { packet.append(contentsOf: $0) }
        packet.append(payload)
        writeAll(packet)
    }

    private func writeAll(_ data: Data) {
        lock.lock()
        defer { lock.unlock() }
        data.withUnsafeBytes { raw in
            guard var base = raw.baseAddress else { return }
            var remaining = raw.count
            while remaining > 0 {
                let written = Darwin.write(fd, base, remaining)
                if written <= 0 {
                    return
                }
                remaining -= written
                base = base.advanced(by: written)
            }
        }
    }
}

final class AudioCaptureController: NSObject, SCStreamOutput {
    private let writer: PacketWriter
    private let queue = DispatchQueue(label: "deep-caption.sc.audio")
    private var stream: SCStream?
    private var lastMs: Int64 = 0
    private var started = false

    init(writer: PacketWriter) {
        self.writer = writer
    }

    func startIfNeeded() {
        guard !started else { return }
        started = true
        Task {
            do {
                try await startCapture()
            } catch {
                fputs("startCapture failed: \(error)\n", stderr)
            }
        }
    }

    func stopIfNeeded() {
        guard started else { return }
        started = false
        Task {
            if let stream {
                try? await stream.stopCapture()
            }
            stream = nil
        }
    }

    private func startCapture() async throws {
        let shareable = try await SCShareableContent.excludingDesktopWindows(false, onScreenWindowsOnly: false)
        guard let display = shareable.displays.first else {
            throw NSError(domain: "deep-caption", code: 1, userInfo: [NSLocalizedDescriptionKey: "No display found"])
        }
        let filter = SCContentFilter(display: display, excludingApplications: [], exceptingWindows: [])

        let config = SCStreamConfiguration()
        config.capturesAudio = true
        config.sampleRate = 16_000
        config.channelCount = 1
        config.width = 2
        config.height = 2
        config.minimumFrameInterval = CMTime(value: 1, timescale: 2)

        let stream = SCStream(filter: filter, configuration: config, delegate: nil)
        try stream.addStreamOutput(self, type: .audio, sampleHandlerQueue: queue)
        try await stream.startCapture()
        self.stream = stream
    }

    func stream(_ stream: SCStream, didOutputSampleBuffer sampleBuffer: CMSampleBuffer, of outputType: SCStreamOutputType) {
        guard outputType == .audio else { return }
        guard let samples = decodeSamples(sampleBuffer) else { return }
        let now = Int64(ProcessInfo.processInfo.systemUptime * 1000.0)
        let t0 = lastMs == 0 ? max(0, now - 30) : lastMs
        lastMs = now
        writer.send(samples: samples, sampleRate: 16_000, t0Ms: t0, t1Ms: now, sourceID: "mac-system")
    }

    private func decodeSamples(_ sampleBuffer: CMSampleBuffer) -> [Float]? {
        var blockBuffer: CMBlockBuffer?
        var list = AudioBufferList(
            mNumberBuffers: 1,
            mBuffers: AudioBuffer(mNumberChannels: 1, mDataByteSize: 0, mData: nil)
        )
        let status = CMSampleBufferGetAudioBufferListWithRetainedBlockBuffer(
            sampleBuffer,
            bufferListSizeNeededOut: nil,
            bufferListOut: &list,
            bufferListSize: MemoryLayout<AudioBufferList>.size,
            blockBufferAllocator: nil,
            blockBufferMemoryAllocator: nil,
            flags: UInt32(kCMSampleBufferFlag_AudioBufferList_Assure16ByteAlignment),
            blockBufferOut: &blockBuffer
        )
        guard status == noErr else { return nil }
        let audioBuffer = list.mBuffers
        guard let mData = audioBuffer.mData else { return nil }

        if let format = CMSampleBufferGetFormatDescription(sampleBuffer),
           let asbdPtr = CMAudioFormatDescriptionGetStreamBasicDescription(format) {
            let asbd = asbdPtr.pointee
            if (asbd.mFormatFlags & kAudioFormatFlagIsFloat) != 0 {
                let count = Int(audioBuffer.mDataByteSize) / MemoryLayout<Float>.size
                let ptr = mData.bindMemory(to: Float.self, capacity: count)
                return Array(UnsafeBufferPointer(start: ptr, count: count))
            }
            if asbd.mBitsPerChannel == 16 {
                let count = Int(audioBuffer.mDataByteSize) / MemoryLayout<Int16>.size
                let ptr = mData.bindMemory(to: Int16.self, capacity: count)
                let src = UnsafeBufferPointer(start: ptr, count: count)
                return src.map { Float($0) / 32768.0 }
            }
        }
        return nil
    }
}

final class BridgeServer {
    private let socketPath: String

    init(socketPath: String) {
        self.socketPath = socketPath
    }

    func run() throws {
        let serverFD = try createServerSocket(socketPath: socketPath)
        defer {
            close(serverFD)
            unlink(socketPath)
        }
        while true {
            let clientFD = accept(serverFD, nil, nil)
            if clientFD < 0 { continue }
            handleClient(clientFD)
        }
    }

    private func handleClient(_ fd: Int32) {
        let writer = PacketWriter(fd: fd)
        let controller = AudioCaptureController(writer: writer)
        controller.startIfNeeded()
        defer {
            controller.stopIfNeeded()
            close(fd)
        }
        while let data = readFrame(fd: fd) {
            guard let msg = try? JSONDecoder().decode(ControlMessage.self, from: data) else {
                continue
            }
            switch msg.action {
            case "start":
                controller.startIfNeeded()
            case "stop":
                controller.stopIfNeeded()
                return
            default:
                break
            }
        }
    }

    private func createServerSocket(socketPath: String) throws -> Int32 {
        unlink(socketPath)
        let fd = socket(AF_UNIX, SOCK_STREAM, 0)
        guard fd >= 0 else {
            throw NSError(domain: "deep-caption", code: 2, userInfo: [NSLocalizedDescriptionKey: "socket create failed"])
        }
        var addr = sockaddr_un()
        addr.sun_family = sa_family_t(AF_UNIX)
        let maxLen = MemoryLayout.size(ofValue: addr.sun_path)
        let utf8 = Array(socketPath.utf8.prefix(maxLen - 1))
        withUnsafeMutableBytes(of: &addr.sun_path) { raw in
            raw.initializeMemory(as: CChar.self, repeating: 0)
            for (idx, byte) in utf8.enumerated() {
                raw[idx] = byte
            }
        }
        let len = socklen_t(MemoryLayout<sa_family_t>.size + utf8.count + 1)
        let bindResult = withUnsafePointer(to: &addr) { ptr in
            ptr.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                Darwin.bind(fd, $0, len)
            }
        }
        guard bindResult == 0 else {
            close(fd)
            throw NSError(domain: "deep-caption", code: 3, userInfo: [NSLocalizedDescriptionKey: "bind failed"])
        }
        guard Darwin.listen(fd, 4) == 0 else {
            close(fd)
            throw NSError(domain: "deep-caption", code: 4, userInfo: [NSLocalizedDescriptionKey: "listen failed"])
        }
        return fd
    }

    private func readFrame(fd: Int32) -> Data? {
        guard let prefix = readExact(fd: fd, size: 4) else { return nil }
        let len = prefix.withUnsafeBytes { $0.load(as: UInt32.self).bigEndian }
        guard let payload = readExact(fd: fd, size: Int(len)) else { return nil }
        return payload
    }

    private func readExact(fd: Int32, size: Int) -> Data? {
        var data = Data(count: size)
        var offset = 0
        while offset < size {
            let readCount = data.withUnsafeMutableBytes { raw -> Int in
                guard let base = raw.baseAddress else { return -1 }
                return Darwin.read(fd, base.advanced(by: offset), size - offset)
            }
            if readCount <= 0 {
                return nil
            }
            offset += readCount
        }
        return data
    }
}

let socketPath = CommandLine.arguments.dropFirst().first ?? "/tmp/deep-caption-mac.sock"
do {
    try BridgeServer(socketPath: socketPath).run()
} catch {
    fputs("mac_audio_capture failed: \(error)\n", stderr)
    exit(1)
}
