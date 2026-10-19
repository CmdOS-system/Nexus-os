import UIKit

@UIApplicationMain
final class NexusAppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.rootViewController = NexusRuntimeViewController()
        window.makeKeyAndVisible()
        self.window = window
        return true
    }
}

final class NexusRuntimeViewController: UIViewController {
    private let frameLabel = UILabel()
    private let marker = UIView()
    private var frame = 0

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red: 11/255, green: 15/255, blue: 25/255, alpha: 1)
        let stack = UIStackView()
        stack.axis = .vertical
        stack.alignment = .leading
        stack.spacing = 18
        stack.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stack)

        let badge = label("IOS SIMULATOR · ARM64", size: 14, color: UIColor(red: 0, green: 0.94, blue: 1, alpha: 1), weight: .bold)
        let title = label("Nexus iOS Runtime", size: 32, color: .white, weight: .bold)
        let detail = label("Native UIKit application", size: 18, color: UIColor(white: 0.78, alpha: 1), weight: .regular)
        frameLabel.font = UIFont.monospacedSystemFont(ofSize: 20, weight: .medium)
        frameLabel.textColor = UIColor(red: 0.44, green: 0.96, blue: 1, alpha: 1)
        frameLabel.text = "Live ARM64 frame: starting"
        marker.backgroundColor = UIColor(red: 0, green: 0.94, blue: 1, alpha: 1)
        marker.layer.cornerRadius = 44
        marker.translatesAutoresizingMaskIntoConstraints = false
        NSLayoutConstraint.activate([
            marker.widthAnchor.constraint(equalToConstant: 88),
            marker.heightAnchor.constraint(equalToConstant: 88)
        ])
        stack.addArrangedSubview(badge)
        stack.addArrangedSubview(title)
        stack.addArrangedSubview(detail)
        stack.addArrangedSubview(marker)
        stack.addArrangedSubview(frameLabel)
        NSLayoutConstraint.activate([
            stack.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 30),
            stack.trailingAnchor.constraint(lessThanOrEqualTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -30),
            stack.centerYAnchor.constraint(equalTo: view.centerYAnchor)
        ])

        Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] _ in
            guard let self else { return }
            self.frame += 1
            self.frameLabel.text = "Live ARM64 frame: \(self.frame)"
            let scale = 0.85 + CGFloat(self.frame % 4) * 0.08
            self.marker.transform = CGAffineTransform(scaleX: scale, y: scale)
            self.persistFrame()
        }
    }

    private func label(_ text: String, size: CGFloat, color: UIColor, weight: UIFont.Weight) -> UILabel {
        let value = UILabel()
        value.text = text
        value.font = UIFont.systemFont(ofSize: size, weight: weight)
        value.textColor = color
        value.numberOfLines = 0
        return value
    }

    private func persistFrame() {
        guard let documents = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first else { return }
        try? "\(frame)\n".write(to: documents.appendingPathComponent("live-frame.txt"), atomically: true, encoding: .utf8)
    }
}
