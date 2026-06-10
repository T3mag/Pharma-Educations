
import UIKit

final class MatchConnectionCanvasView: UIView {
    
    struct Line {
        let start: CGPoint
        let end: CGPoint
    }
    
    private var lines: [Line] = []
    private var temporaryLine: Line?
    
    override class var layerClass: AnyClass {
        CAShapeLayer.self
    }
    
    private var shapeLayer: CAShapeLayer {
        layer as! CAShapeLayer
    }
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        isUserInteractionEnabled = false
        backgroundColor = .clear
        shapeLayer.fillColor = UIColor.clear.cgColor
        shapeLayer.strokeColor = Colors.rose.cgColor
        shapeLayer.lineWidth = 3
        shapeLayer.lineCap = .round
    }
    
    func setLines(_ lines: [Line]) {
        self.lines = lines
        setNeedsLayout()
    }
    
    func setTemporaryLine(_ line: Line?) {
        temporaryLine = line
        setNeedsLayout()
    }
    
    override func layoutSubviews() {
        super.layoutSubviews()
        
        let path = UIBezierPath()
        for line in lines {
            addCurve(for: line, to: path)
        }
        
        if let temporaryLine {
            addCurve(for: temporaryLine, to: path)
        }
        
        shapeLayer.path = path.cgPath
    }
    
    private func addCurve(for line: Line, to path: UIBezierPath) {
        let distance = abs(line.end.x - line.start.x)
        let controlOffset = max(40, distance * 0.45)
        let firstControlPoint = CGPoint(x: line.start.x + controlOffset, y: line.start.y)
        let secondControlPoint = CGPoint(x: line.end.x - controlOffset, y: line.end.y)
        
        path.move(to: line.start)
        path.addCurve(
            to: line.end,
            controlPoint1: firstControlPoint,
            controlPoint2: secondControlPoint
        )
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
}
