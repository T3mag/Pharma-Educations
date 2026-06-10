import UIKit

final class MinigameCollectionViewHandler: NSObject, UICollectionViewDataSource, UICollectionViewDelegateFlowLayout {
    var onCellTap: ((MiniGamesType) -> Void)?
    
    private var items: [ListItem<MinigameItem>] = [.title]
    
    init(with minigames: [MinigameItem] = []) {
        items = [.title] + minigames.map{ ListItem.item($0)}
    }
    
    func updateMinigames(with minigames: [MinigameItem]) {
        items = [.title] + minigames.map{ ListItem.item($0)}
    }
    
    func collectionView(_ collectionView: UICollectionView,
                        numberOfItemsInSection section: Int
    ) -> Int {
        items.count
    }
    
    func collectionView(_ collectionView: UICollectionView,
                        cellForItemAt indexPath: IndexPath
    ) -> UICollectionViewCell {
        
        switch items[indexPath.item] {
        case .title:
            guard let cell = collectionView.dequeueReusableCell(
                withReuseIdentifier: MinigameTitleCollectionViewCell.reuseIdentifier, for: indexPath
            ) as? MinigameTitleCollectionViewCell else {
                return UICollectionViewCell()
            }
            
            return cell
            
        case .item(let item):
            guard let cell = collectionView.dequeueReusableCell(
                withReuseIdentifier: MinigameCollectionViewCell.reuseIdentifier, for: indexPath
            ) as? MinigameCollectionViewCell else {
                return UICollectionViewCell()
            }
            
            cell.configure(item: item)
            return cell
        }
    }
    
    func collectionView(
        _ collectionView: UICollectionView,
        layout collectionViewLayout: UICollectionViewLayout,
        sizeForItemAt indexPath: IndexPath
    ) -> CGSize {
        
        switch items[indexPath.item] {
        case .title:
            let spacing = MinigameConstants.TitleCell.spacingStackview
            let indents = MinigameConstants.TitleCell.indentsFromContentView * 2
            let titleFontSize = MinigameFonts.TitleCell.titleFont.lineHeight
            let subtitleFontSize = MinigameFonts.TitleCell.subtitleFont.lineHeight * 2
            
            let height = indents + titleFontSize + spacing + subtitleFontSize
            let width = collectionView.bounds.width

            return CGSize(width: width, height: height)
        case .item(_):
            let spacing: CGFloat = 16
            let itemsPerRow: CGFloat = 2

            let totalSpacing = spacing * (itemsPerRow - 1)
            let availableWidth = collectionView.bounds.width - totalSpacing
            let itemWidth = availableWidth / itemsPerRow

            return CGSize(width: itemWidth, height: itemWidth)
        }
    }
    
    func collectionView(_ collectionView: UICollectionView, didSelectItemAt indexPath: IndexPath) {
        collectionView.deselectItem(at: indexPath, animated: true)
        guard let cell = collectionView.cellForItem(at: indexPath) as? MinigameCollectionViewCell else {
            return
        }
        
        guard let type = cell.miniGameType else {
            return
        }
        onCellTap?(type)
    }
}
