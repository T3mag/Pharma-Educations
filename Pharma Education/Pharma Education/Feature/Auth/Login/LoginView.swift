import UIKit

final class LoginView: UIView {
    
    var onLoginTap: ((_ email: String,
                      _ password: String) -> Void)?
    var onRegisterTap: (() -> Void)?
    
    private lazy var loginButtonContainer: UIView = AuxiliaryUIViews.stackViewContainer
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fill
        return stackView
    }()
    
    private lazy var centreStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fill
        stackView.spacing = 10
        return stackView
    }()
    
    private lazy var topSpaceView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var bottomSpaceView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .black
        label.text = Texts.Login.title
        label.numberOfLines = 5
        label.textAlignment = .center
        label.font = Fonts.Login.title
        
        return label
    }()
    
    private lazy var loginTextFieldHeader: UILabel = {
       let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Login.loginHeader
        return label
    }()
    
    private lazy var loginTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .secondarySystemBackground
        textField.placeholder = Texts.Login.loginPlaceholder
        textField.autocapitalizationType = .none
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Login.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var passwordTextFieldHeader: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Login.passwordHeader
        return label
    }()
    
    private lazy var passwordTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .secondarySystemBackground
        textField.placeholder = Texts.Login.passwordPlaceholder
        textField.autocapitalizationType = .none
        textField.configurePasswordToggle()
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Login.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var registrButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.setTitle(Texts.Login.registrationButton, for: .normal)
        button.backgroundColor = .none
        button.setTitleColor(.black, for: .normal)
        button.titleLabel?.numberOfLines = 2
        button.titleLabel?.textAlignment = .center
        button.titleLabel?.font = Fonts.Login.registrationButtonFont
        button.addTarget(self, action: #selector(registrationButtonTapped), for: .touchUpInside)
        return button
    }()
    
    private lazy var loginButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = .secondarySystemBackground
        button.setTitle(Texts.Login.loginButton, for: .normal)
        button.setTitleColor(.black, for: .normal)
        button.titleLabel?.font = Fonts.Login.authorisationButtonFont
        button.addTarget(self, action: #selector(loginButtonTapped), for: .touchUpInside)
        button.layer.cornerRadius = Constants.Login.cornerRadius
        return button
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        
        setupHierarchy()
        setupLayout()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
        
    }
    
    private func setupLayout() {
        
        backgroundColor = .systemBackground
        addSubview(rootStackView)
        
        NSLayoutConstraint.activate([
            rootStackView.topAnchor.constraint(equalTo: safeAreaLayoutGuide.topAnchor),
            rootStackView.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor,
                                                   constant: Constants.Login.indentsFromSafeArea),
            rootStackView.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor,
                                                    constant: -Constants.Login.indentsFromSafeArea),
            rootStackView.bottomAnchor.constraint(equalTo: safeAreaLayoutGuide.bottomAnchor,
                                                  constant: -Constants.Login.indentsFromSafeArea)
        ])
        
        NSLayoutConstraint.activate([
            topSpaceView.heightAnchor.constraint(equalTo: bottomSpaceView.heightAnchor, multiplier: 0.3),
            
            passwordTextField.heightAnchor.constraint(equalToConstant: Constants.Login.heightTextField),
            loginTextField.heightAnchor.constraint(equalToConstant: Constants.Login.heightTextField),

            loginButton.widthAnchor.constraint(equalTo: rootStackView.widthAnchor, multiplier: 0.8),
            loginButton.heightAnchor.constraint(equalToConstant: Constants.Login.heightButton),
            loginButton.centerXAnchor.constraint(equalTo: loginButtonContainer.centerXAnchor),
            loginButton.topAnchor.constraint(equalTo: loginButtonContainer.topAnchor),
            loginButton.bottomAnchor.constraint(equalTo: loginButtonContainer.bottomAnchor)
        ])
    }
    
    private func setupHierarchy() {
        loginButtonContainer.addSubview(loginButton)
        
        rootStackView.addArrangedSubview(titleLabel)
        rootStackView.addArrangedSubview(topSpaceView)
        rootStackView.addArrangedSubview(centreStackView)
        rootStackView.addArrangedSubview(bottomSpaceView)
        rootStackView.addArrangedSubview(loginButtonContainer)
        
        centreStackView.addArrangedSubview(loginTextFieldHeader)
        centreStackView.addArrangedSubview(loginTextField)
        centreStackView.addArrangedSubview(passwordTextFieldHeader)
        centreStackView.addArrangedSubview(passwordTextField)
        centreStackView.addArrangedSubview(registrButton)
    }
    
    @objc
    private func loginButtonTapped() {
        onLoginTap?(loginTextField.text ?? "",
                    passwordTextField.text ?? "")
    }
    
    @objc
    private func registrationButtonTapped() {
        onRegisterTap?()
    }
    
}

