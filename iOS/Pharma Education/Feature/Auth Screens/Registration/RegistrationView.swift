import UIKit

final class RegistrationView: UIView {
    
    var onRegisterTap: ((_ email: String,
                         _ password: String,
                         _ confirmPassword: String,
                         _ fullname: String
                        ) -> Void)?
    
    private var checkBoxFlag = false
    
    private lazy var registrationButtonContainer: UIView = AuxiliaryUIViews.stackViewContainer
    
    private lazy var backgroundDesign: UIView = BackgroundDesignView()
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fill
        stackView.spacing = RegistrationConstants.spacingRootStackView
        return stackView
    }()
    
    private lazy var topStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = RegistrationConstants.spacingTitleStackView
        return stackView
    }()
    
    private lazy var centreStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fill
        stackView.spacing = RegistrationConstants.spacingCenterStackView
        return stackView
    }()
    
    private lazy var policyStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .horizontal
        stackView.alignment = .leading
        stackView.spacing = RegistrationConstants.spacingPolicyStackView
        return stackView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = RegistrationFonts.titleFont
        label.text = RegistrationTexts.title
        label.textColor = .black
        label.textAlignment = .center
        label.numberOfLines = 1
        return label
    }()
    
    private lazy var subtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = RegistrationFonts.subtitleFont
        label.text = RegistrationTexts.subtitle
        label.textColor = .gray
        label.textAlignment = .center
        label.numberOfLines = 1
        return label
    }()
    
    private lazy var fullNameTextField: UITextField = {
        let textField = UITextField()
        textField.placeholder = RegistrationTexts.fullNamePlaceholder
        return textField
    }()
    
    private lazy var emailTextField: UITextField = {
        let textField = UITextField()
        textField.placeholder = RegistrationTexts.emailPlaceholder
        return textField
    }()
    
    private lazy var passwordTextField: UITextField = {
        let textField = UITextField()
        textField.configurePasswordToggle()
        textField.placeholder = RegistrationTexts.passwordPlaceholder
        return textField
    }()
    
    private lazy var confirmPasswordTextField: UITextField = {
        let textField = UITextField()
        textField.configurePasswordToggle()
        textField.placeholder = RegistrationTexts.confirmPasswordPlaceholder
        return textField
    }()
    
    private lazy var checkBoxButton: UIButton = {
        let button = UIButton(type: .system)
        button.translatesAutoresizingMaskIntoConstraints = false
        button.tintColor = Colors.rose
        button.setImage(UIImage(systemName: "square"), for: .normal)
        button.addTarget(self, action: #selector(checkBoxTapped), for: .touchUpInside)
        return button
    }()
    
    private lazy var policyLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = RegistrationFonts.policyFont
        label.text = RegistrationTexts.policyAgreement
        label.textColor = .gray
        label.numberOfLines = 2
        return label
    }()
    
    private lazy var registrationButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = Colors.rose
        button.setTitle(RegistrationTexts.registrationButton, for: .normal)
        button.titleLabel?.font = RegistrationFonts.registartionButtonFont
        button.layer.cornerRadius = RegistrationConstants.heightButton / 3
        button.addTarget(self, action: #selector(registrationButtonTapped), for: .touchUpInside)
        return button
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        
        setupTextFields([fullNameTextField, emailTextField, passwordTextField, confirmPasswordTextField])
        setupHierarchy()
        setupLayout()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    private func setupTextFields(_ textFields: [UITextField]) {
        for textField in textFields {
            textField.translatesAutoresizingMaskIntoConstraints = false
            textField.backgroundColor = .white
            textField.autocapitalizationType = .none
            textField.leftViewMode = .always
            textField.clipsToBounds = true
            textField.layer.cornerRadius = RegistrationConstants.heightTextField / 2.5
            textField.leftView = AuxiliaryUIViews.leftViewForTextField
        }
    }
    
    private func setupLayout() {
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            backgroundDesign.topAnchor.constraint(
                equalTo: topAnchor),
            backgroundDesign.leadingAnchor.constraint(
                equalTo: leadingAnchor),
            backgroundDesign.trailingAnchor.constraint(
                equalTo: trailingAnchor),
            backgroundDesign.bottomAnchor.constraint(
                equalTo: bottomAnchor),
            
            rootStackView.topAnchor.constraint(
                equalTo: safeAreaLayoutGuide.topAnchor,
                constant: RegistrationConstants.indentsFromSafeArea),
            rootStackView.leadingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.leadingAnchor,
                constant: RegistrationConstants.indentsFromSafeArea),
            rootStackView.trailingAnchor.constraint(
                equalTo: safeAreaLayoutGuide.trailingAnchor,
                constant: -RegistrationConstants.indentsFromSafeArea)
        ])
        
        NSLayoutConstraint.activate([
            fullNameTextField.heightAnchor.constraint(
                equalToConstant: RegistrationConstants.heightTextField),
            emailTextField.heightAnchor.constraint(
                equalToConstant: RegistrationConstants.heightTextField),
            passwordTextField.heightAnchor.constraint(
                equalToConstant: RegistrationConstants.heightTextField),
            confirmPasswordTextField.heightAnchor.constraint(
                equalToConstant: RegistrationConstants.heightTextField),
            checkBoxButton.heightAnchor.constraint(
                equalToConstant: RegistrationConstants.checkBoxSize),
            checkBoxButton.widthAnchor.constraint(
                equalToConstant: RegistrationConstants.checkBoxSize),
            registrationButton.heightAnchor.constraint(
                equalToConstant: RegistrationConstants.heightButton)
        ])
    }
    
    private func setupHierarchy() {
        
        addSubview(backgroundDesign)
        addSubview(rootStackView)
        
        rootStackView.addArrangedSubview(topStackView)
        rootStackView.addArrangedSubview(centreStackView)
        rootStackView.addArrangedSubview(registrationButton)
        
        topStackView.addArrangedSubview(titleLabel)
        topStackView.addArrangedSubview(subtitleLabel)
        
        centreStackView.addArrangedSubview(fullNameTextField)
        centreStackView.addArrangedSubview(emailTextField)
        centreStackView.addArrangedSubview(passwordTextField)
        centreStackView.addArrangedSubview(confirmPasswordTextField)
        centreStackView.addArrangedSubview(policyStackView)
        
        policyStackView.addArrangedSubview(checkBoxButton)
        policyStackView.addArrangedSubview(policyLabel)
    }
    
    @objc
    private func checkBoxTapped() {
        if !checkBoxFlag {
            checkBoxFlag = true
            checkBoxButton.setImage(UIImage(systemName: "checkmark.square.fill"), for: .normal)
        } else {
            checkBoxFlag = false
            checkBoxButton.setImage(UIImage(systemName: "square"), for: .normal)
        }
    }
    
    @objc
    private func registrationButtonTapped() {
        onRegisterTap?(
            emailTextField.text ?? "",
            passwordTextField.text ?? "",
            confirmPasswordTextField.text ?? "",
            fullNameTextField.text ?? ""
        )
    }
        
}
