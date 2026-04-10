// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "mac_audio_capture",
    platforms: [
        .macOS(.v13),
    ],
    products: [
        .executable(name: "mac_audio_capture", targets: ["mac_audio_capture"]),
    ],
    targets: [
        .executableTarget(
            name: "mac_audio_capture",
            linkerSettings: [
                .linkedFramework("ScreenCaptureKit"),
                .linkedFramework("AVFoundation"),
            ]
        ),
    ]
)
