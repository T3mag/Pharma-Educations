import UIKit

final class TreeLinesView: UIView {
    
    var depth: Int = 0 {
        didSet { setNeedsDisplay() }
    }

    var isLastChild: Bool = false {
        didSet { setNeedsDisplay() }
    }
    
    var parentLevels: [Int] = [] {
        didSet { setNeedsDisplay() }
    }
    
    var drawsChildConnector: Bool = false {
        didSet { setNeedsDisplay() }
    }
    
    private let step: CGFloat = 34
    private let startX: CGFloat = 24

    override func draw(_ rect: CGRect) {
        let color = Colors.rose.withAlphaComponent(0.6)
        color.setStroke()

        let centerY = rect.midY
        var posX: CGFloat
        var path: UIBezierPath
        
        if drawsChildConnector {
            posX = calculatePosX(CGFloat(depth))
            path = makeDashedPath()
            
            path.move(to: CGPoint(x: posX, y: centerY))
            path.addLine(to: CGPoint(x: posX, y: rect.height))
            path.stroke()
        }
        
        guard depth > 0 else {
            return
        }

        for level in parentLevels {
            posX = calculatePosX(CGFloat(level - 1))
            path = makeDashedPath()
            
            path.move(
                to: CGPoint(x: posX, y: 0)
            )
            path.addLine(
                to: CGPoint(
                    x: posX,
                    y: rect.height)
            )
            path.stroke()
        }

        posX = calculatePosX(CGFloat(depth - 1))
        path = makeDashedPath()

        path.move(
            to: CGPoint(x: posX,y: 0)
        )
        path.addLine(to: CGPoint(
            x: posX,
            y: isLastChild ? centerY : rect.height
        ))

        path.move(
            to: CGPoint(x: posX, y: centerY))
        path.addLine(
            to: CGPoint(x: posX + step, y: centerY))
        path.stroke()
    }
    
    private func calculatePosX(_ value: CGFloat) -> CGFloat {
        startX + CGFloat(value) * step
    }
    
    private func makeDashedPath() -> UIBezierPath {
        let path = UIBezierPath()
        path.lineWidth = 1
        path.setLineDash([3, 3], count: 2, phase: 0)
        return path
    }
}
