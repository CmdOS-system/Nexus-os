import UIKit

@UIApplicationMain
final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    func application(_ application: UIApplication, didFinishLaunchingWithOptions options: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        window.rootViewController = GameViewController()
        window.makeKeyAndVisible()
        self.window = window
        return true
    }
}

final class GameViewController: UIViewController {
    private var board = Array(repeating: 0, count: 16)
    private var cells: [UILabel] = []
    private let scoreLabel = UILabel()
    private var score = 0
    private var automaticMove = 0

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = UIColor(red: 0.04, green: 0.07, blue: 0.12, alpha: 1)
        let title = UILabel(); title.text = "2048"; title.textColor = .white
        title.font = .systemFont(ofSize: 52, weight: .heavy); title.textAlignment = .center
        let subtitle = UILabel(); subtitle.text = "Nexus · iOS ARM64"; subtitle.textColor = .cyan
        subtitle.font = .systemFont(ofSize: 16, weight: .semibold); subtitle.textAlignment = .center
        scoreLabel.textColor = .white; scoreLabel.textAlignment = .center
        scoreLabel.font = .monospacedDigitSystemFont(ofSize: 20, weight: .bold)
        scoreLabel.text = "SCORE  0"

        let boardStack = UIStackView(); boardStack.axis = .vertical; boardStack.spacing = 8
        boardStack.distribution = .fillEqually
        for _ in 0..<4 {
            let row = UIStackView(); row.axis = .horizontal; row.spacing = 8; row.distribution = .fillEqually
            for _ in 0..<4 {
                let cell = UILabel(); cell.textAlignment = .center; cell.layer.cornerRadius = 12
                cell.layer.masksToBounds = true; cell.font = .systemFont(ofSize: 30, weight: .heavy)
                cell.backgroundColor = UIColor(red: 0.10, green: 0.16, blue: 0.24, alpha: 1)
                cells.append(cell); row.addArrangedSubview(cell)
            }
            boardStack.addArrangedSubview(row)
        }
        let reset = UIButton(type: .system); reset.setTitle("New game", for: .normal)
        reset.setTitleColor(.black, for: .normal); reset.backgroundColor = .cyan
        reset.layer.cornerRadius = 12; reset.titleLabel?.font = .boldSystemFont(ofSize: 18)
        reset.addTarget(self, action: #selector(newGame), for: .touchUpInside)
        let layout = UIStackView(arrangedSubviews: [title, subtitle, scoreLabel, boardStack, reset])
        layout.axis = .vertical; layout.spacing = 18; layout.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(layout)
        NSLayoutConstraint.activate([
            layout.leadingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.leadingAnchor, constant: 28),
            layout.trailingAnchor.constraint(equalTo: view.safeAreaLayoutGuide.trailingAnchor, constant: -28),
            layout.centerYAnchor.constraint(equalTo: view.centerYAnchor),
            boardStack.heightAnchor.constraint(equalTo: layout.widthAnchor),
            reset.heightAnchor.constraint(equalToConstant: 52)
        ])
        for direction in [UISwipeGestureRecognizer.Direction.left, .right, .up, .down] {
            let gesture = UISwipeGestureRecognizer(target: self, action: #selector(swiped(_:)))
            gesture.direction = direction; view.addGestureRecognizer(gesture)
        }
        newGame()
        Timer.scheduledTimer(withTimeInterval: 1.4, repeats: true) { [weak self] _ in
            guard let self else { return }
            let directions: [UISwipeGestureRecognizer.Direction] = [.left, .up, .right, .down]
            self.move(directions[self.automaticMove % directions.count]); self.automaticMove += 1
        }
    }

    @objc private func newGame() {
        board = Array(repeating: 0, count: 16); score = 0; automaticMove = 0
        addTile(); addTile(); render()
    }
    @objc private func swiped(_ gesture: UISwipeGestureRecognizer) { move(gesture.direction) }

    private func move(_ direction: UISwipeGestureRecognizer.Direction) {
        var changed = false
        for line in 0..<4 {
            var indexes = (0..<4).map { offset -> Int in
                switch direction {
                case .left: return line * 4 + offset
                case .right: return line * 4 + (3 - offset)
                case .up: return offset * 4 + line
                default: return (3 - offset) * 4 + line
                }
            }
            let old = indexes.map { board[$0] }
            let values = old.filter { $0 != 0 }; var merged: [Int] = []; var cursor = 0
            while cursor < values.count {
                if cursor + 1 < values.count && values[cursor] == values[cursor + 1] {
                    let value = values[cursor] * 2; merged.append(value); score += value; cursor += 2
                } else { merged.append(values[cursor]); cursor += 1 }
            }
            merged += Array(repeating: 0, count: 4 - merged.count)
            if old != merged { changed = true }
            for (offset, index) in indexes.enumerated() { board[index] = merged[offset] }
            indexes.removeAll(keepingCapacity: false)
        }
        if changed { addTile() }
        render()
    }
    private func addTile() {
        let empty = board.indices.filter { board[$0] == 0 }
        if let index = empty.randomElement() { board[index] = Int.random(in: 0..<10) == 0 ? 4 : 2 }
    }
    private func render() {
        scoreLabel.text = "SCORE  \(score)"
        for (index, value) in board.enumerated() {
            let cell = cells[index]; cell.text = value == 0 ? "" : String(value)
            let shade = min(0.92, 0.22 + Double(value == 0 ? 0 : value.trailingZeroBitCount) * 0.045)
            cell.backgroundColor = value == 0
                ? UIColor(red: 0.10, green: 0.16, blue: 0.24, alpha: 1)
                : UIColor(red: 0.0, green: shade, blue: 0.95, alpha: 1)
            cell.textColor = value >= 128 ? .white : .black
        }
    }
}
