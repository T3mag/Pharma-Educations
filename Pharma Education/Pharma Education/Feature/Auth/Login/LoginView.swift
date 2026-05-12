import UIKit

final class LoginView: UIView {
    
    var onLoginTap: ((_ email: String,
                      _ password: String) -> Void)?
    var onRegisterTap: (() -> Void)?
    
    private lazy var backgroundDesignView: UIView = BackgroundDesignView()
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.spacing = 40
        return stackView
    }()
    
    private lazy var titleStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .leading
        stackView.spacing = 10
        return stackView
    }()
    
    private lazy var centreStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fill
        stackView.spacing = 20
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
        label.numberOfLines = 1
        label.textAlignment = .left
        label.text = LoginTexts.title
        label.font = LoginFonts.titleFont
        
        return label
    }()
    
    private lazy var subtitleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.numberOfLines = 2
        label.textAlignment = .left
        label.text = LoginTexts.subtitle
        label.font = LoginFonts.subtitleFont
        return label
    }()
    
    private lazy var loginTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .white
        textField.placeholder = LoginTexts.loginPlaceholder
        textField.autocapitalizationType = .none
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = LoginConstants.heightTextField / 2.5
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var passwordTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .white
        textField.placeholder = LoginTexts.passwordPlaceholder
        textField.autocapitalizationType = .none
        textField.configurePasswordToggle()
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.clipsToBounds = true
        textField.layer.cornerRadius = LoginConstants.heightTextField / 2.5
        return textField
    }()
    
    private lazy var forgotPassword: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.setTitle(LoginTexts.forgotPassword, for: .normal)
        button.backgroundColor = .none
        button.setTitleColor(Colors.rose, for: .normal)
        button.titleLabel?.numberOfLines = 2
        button.titleLabel?.textAlignment = .center
        button.titleLabel?.font = LoginFonts.forgotPasswordButtonFont
        return button
    }()
    
    private lazy var registrButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.setTitle(LoginTexts.registrationButton, for: .normal)
        button.backgroundColor = .none
        button.setTitleColor(.white, for: .normal)
        button.titleLabel?.numberOfLines = 2
        button.titleLabel?.textAlignment = .center
        button.titleLabel?.font = LoginFonts.registrationButtonFont
        button.addTarget(self, action: #selector(registrationButtonTapped), for: .touchUpInside)
        return button
    }()
    
    private lazy var loginButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = Colors.rose
        button.setTitle(LoginTexts.loginButton, for: .normal)
        button.titleLabel?.font = LoginFonts.authorisationButtonFont
        button.setTitleColor(.white, for: .normal)
        button.addTarget(self, action: #selector(loginButtonTapped), for: .touchUpInside)
        button.layer.cornerRadius = LoginConstants.cornerRadius
        button.layer.cornerRadius = LoginConstants.heightButton / 3
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
        
        backgroundColor = Colors.lavenderBlush
        
        NSLayoutConstraint.activate([
            backgroundDesignView.topAnchor.constraint(equalTo: topAnchor),
            backgroundDesignView.leadingAnchor.constraint(equalTo: leadingAnchor),
            backgroundDesignView.trailingAnchor.constraint(equalTo: trailingAnchor),
            backgroundDesignView.bottomAnchor.constraint(equalTo: bottomAnchor),
            
            rootStackView.topAnchor.constraint(equalTo: safeAreaLayoutGuide.topAnchor),
            rootStackView.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor,
                                                   constant: LoginConstants.indentsFromSafeArea),
            rootStackView.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor,
                                                    constant: -LoginConstants.indentsFromSafeArea)
        ])
        
        NSLayoutConstraint.activate([
            passwordTextField.heightAnchor.constraint(equalToConstant: LoginConstants.heightTextField),
            loginTextField.heightAnchor.constraint(equalToConstant: LoginConstants.heightTextField),
            loginButton.heightAnchor.constraint(equalToConstant: LoginConstants.heightButton),
            
            registrButton.bottomAnchor.constraint(equalTo: safeAreaLayoutGuide.bottomAnchor,
                                                  constant: -LoginConstants.indentsFromSafeArea),
            registrButton.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor,
                                                   constant: LoginConstants.indentsFromSafeArea),
            registrButton.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor,
                                                    constant: -LoginConstants.indentsFromSafeArea)
        ])
        
    }
    
    private func setupHierarchy() {
        addSubview(backgroundDesignView)
        addSubview(rootStackView)
        addSubview(registrButton)
        
        rootStackView.addArrangedSubview(titleStackView)
        rootStackView.addArrangedSubview(centreStackView)
        rootStackView.addArrangedSubview(loginButton)
        
        titleStackView.addArrangedSubview(titleLabel)
        titleStackView.addArrangedSubview(subtitleLabel)
        
        centreStackView.addArrangedSubview(loginTextField)
        centreStackView.addArrangedSubview(passwordTextField)
        centreStackView.addArrangedSubview(forgotPassword)
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

