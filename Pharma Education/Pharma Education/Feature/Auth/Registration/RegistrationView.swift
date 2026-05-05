import UIKit

final class RegistartionView: UIView {
    
    var onRegisterTap: (() -> Void)?
    
    private lazy var registrationButtonContainer: UIView = AuxiliaryUIViews.stackViewContainer
    
    private lazy var scrollView: UIScrollView = {
        let scrollView = UIScrollView()
        scrollView.translatesAutoresizingMaskIntoConstraints = false
        return scrollView
    }()

    private lazy var contentView: UIView = {
        let view = UIView()
        view.translatesAutoresizingMaskIntoConstraints = false
        return view
    }()
    
    private lazy var rootStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fill
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
    
    private lazy var centreStackView: UIStackView = {
        let stackView = UIStackView()
        stackView.translatesAutoresizingMaskIntoConstraints = false
        stackView.axis = .vertical
        stackView.alignment = .fill
        stackView.distribution = .fill
        stackView.spacing = 10
        return stackView
    }()
    
    private lazy var titleLabel: UILabel = {
        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.font = Fonts.Registration.title
        label.text = Texts.Registration.title
        label.textColor = .black
        label.textAlignment = .center
        label.numberOfLines = 2
        return label
    }()
    
    private lazy var surnameTextFieldHeader: UILabel = {
       let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Registration.surnameHeader
        return label
    }()
    
    private lazy var surnameTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .secondarySystemBackground
        textField.placeholder = Texts.Registration.surnamePlaceholder
        textField.autocapitalizationType = .none
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Registration.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var nameTextFieldHeader: UILabel = {
       let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Registration.nameHaeader
        return label
    }()
    
    private lazy var nameTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .secondarySystemBackground
        textField.placeholder = Texts.Registration.namePlaceholder
        textField.autocapitalizationType = .none
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Registration.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var lastnameTextFieldHeader: UILabel = {
       let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Registration.lastnameHeader
        return label
    }()
    
    private lazy var lastnameTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .secondarySystemBackground
        textField.placeholder = Texts.Registration.lastnamePlaceholder
        textField.autocapitalizationType = .none
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Registration.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var emailTextFieldHeader: UILabel = {
       let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Registration.emailHeader
        return label
    }()
    
    private lazy var emailTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .secondarySystemBackground
        textField.placeholder = Texts.Registration.emailPlaceholder
        textField.autocapitalizationType = .none
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Registration.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var birthdayTextFieldHeader: UILabel = {
       let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Registration.birthdayHeader
        return label
    }()
    
    private lazy var birthdateTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.placeholder = Texts.Registration.birthdayPlaceholder
        textField.inputView = datePicker
        textField.inputAccessoryView = dateToolBar
        textField.backgroundColor = .secondarySystemBackground
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Registration.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var passwordTextFieldHeader: UILabel = {
       let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Registration.passwordHeader
        return label
    }()
    
    private lazy var passwordTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .secondarySystemBackground
        textField.placeholder = Texts.Registration.passwordPlaceholder
        textField.autocapitalizationType = .none
        textField.configurePasswordToggle()
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Registration.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var confirmPasswordTextFieldHeader: UILabel = {
       let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .gray
        label.text = Texts.Registration.repeatpasswordHeader
        return label
    }()
    
    private lazy var confirmPasswordTextField: UITextField = {
        let textField = UITextField()
        textField.translatesAutoresizingMaskIntoConstraints = false
        textField.backgroundColor = .secondarySystemBackground
        textField.placeholder = Texts.Registration.repeatpasswordPlaceholder
        textField.autocapitalizationType = .none
        textField.configurePasswordToggle()
        textField.leftView = AuxiliaryUIViews.leftViewForTextField
        textField.leftViewMode = .always
        textField.layer.cornerRadius = Constants.Registration.cornerRadius
        textField.clipsToBounds = true
        return textField
    }()
    
    private lazy var registartionButton: UIButton = {
        let button = UIButton()
        button.translatesAutoresizingMaskIntoConstraints = false
        button.backgroundColor = .secondarySystemBackground
        button.setTitle(Texts.Registration.registrationButton, for: .normal)
        button.setTitleColor(.black, for: .normal)
        button.titleLabel?.font = Fonts.Registration.registrationButtonFont
        button.addTarget(self, action: #selector(registrationButtonTapped), for: .touchUpInside)
        button.layer.cornerRadius = Constants.Registration.cornerRadius
        return button
    }()
    
    private lazy var datePicker: UIDatePicker = {
        let datePicker = UIDatePicker()
        datePicker.datePickerMode = .date
        datePicker.preferredDatePickerStyle = .wheels
        datePicker.maximumDate = .now
        datePicker.locale = Locale(identifier: "ru_RU")
        return datePicker
    }()
    
    private lazy var dateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "dd.MM.yyyy"
        return formatter
    }()
    
    private lazy var dateToolBar: UIToolbar = {
        let toolBar = UIToolbar()
        toolBar.sizeToFit()
        
        let doneButton = UIBarButtonItem(
            title: "Готово",
            style: .plain,
            target: self,
            action: #selector(doneDateTapped)
        )

        toolBar.items = [
            UIBarButtonItem(barButtonSystemItem: .flexibleSpace, target: nil, action: nil),
            doneButton
        ]

        return toolBar
        
    }()
    
    override init(frame: CGRect) {
        super.init(frame: frame)
        
        setupHierarchy()
        setupLayout()
    }
    
    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }
    
    func setupLayout() {
        backgroundColor = .systemBackground
        
        NSLayoutConstraint.activate([
            scrollView.topAnchor.constraint(equalTo: safeAreaLayoutGuide.topAnchor),
            scrollView.leadingAnchor.constraint(equalTo: safeAreaLayoutGuide.leadingAnchor),
            scrollView.trailingAnchor.constraint(equalTo: safeAreaLayoutGuide.trailingAnchor),
            scrollView.bottomAnchor.constraint(equalTo: safeAreaLayoutGuide.bottomAnchor),

            contentView.topAnchor.constraint(equalTo: scrollView.contentLayoutGuide.topAnchor),
            contentView.leadingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.leadingAnchor),
            contentView.trailingAnchor.constraint(equalTo: scrollView.contentLayoutGuide.trailingAnchor),
            contentView.bottomAnchor.constraint(equalTo: scrollView.contentLayoutGuide.bottomAnchor),

            contentView.widthAnchor.constraint(equalTo: scrollView.frameLayoutGuide.widthAnchor),
            
            rootStackView.topAnchor.constraint(equalTo: contentView.topAnchor),
            rootStackView.leadingAnchor.constraint(equalTo: contentView.leadingAnchor,
                                                   constant: Constants.Registration.indentsFromSafeArea),
            rootStackView.trailingAnchor.constraint(equalTo: contentView.trailingAnchor,
                                                    constant: -Constants.Registration.indentsFromSafeArea),
            
            rootStackView.bottomAnchor.constraint(equalTo: contentView.bottomAnchor,
                                                  constant: -Constants.Registration.indentsFromSafeArea)
        ])
        
        NSLayoutConstraint.activate([
            topSpaceView.heightAnchor.constraint(equalToConstant: Constants.Registration.indentsFromSafeArea),
            bottomSpaceView.heightAnchor.constraint(equalToConstant: Constants.Registration.indentsFromSafeArea * 3),
            
            surnameTextField.heightAnchor.constraint(equalToConstant: Constants.Registration.heightTextField),
            nameTextField.heightAnchor.constraint(equalToConstant: Constants.Registration.heightTextField),
            lastnameTextField.heightAnchor.constraint(equalToConstant: Constants.Registration.heightTextField),
            emailTextField.heightAnchor.constraint(equalToConstant: Constants.Registration.heightTextField),
            birthdateTextField.heightAnchor.constraint(equalToConstant: Constants.Registration.heightTextField),
            passwordTextField.heightAnchor.constraint(equalToConstant: Constants.Registration.heightTextField),
            confirmPasswordTextField.heightAnchor.constraint(equalToConstant: Constants.Registration.heightTextField),
            registartionButton.widthAnchor.constraint(equalTo: rootStackView.widthAnchor, multiplier: 0.8),
            registartionButton.centerXAnchor.constraint(equalTo: registrationButtonContainer.centerXAnchor),
            registartionButton.topAnchor.constraint(equalTo: registrationButtonContainer.topAnchor),
            registartionButton.bottomAnchor.constraint(equalTo: registrationButtonContainer.bottomAnchor)
        ])
    }
    
    func setupHierarchy() {
        addSubview(scrollView)
        scrollView.addSubview(contentView)
        contentView.addSubview(rootStackView)
        
        registrationButtonContainer.addSubview(registartionButton)
        
        rootStackView.addArrangedSubview(titleLabel)
        rootStackView.addArrangedSubview(topSpaceView)
        rootStackView.addArrangedSubview(centreStackView)
        rootStackView.addArrangedSubview(bottomSpaceView)
        rootStackView.addArrangedSubview(registrationButtonContainer)
        
        centreStackView.addArrangedSubview(surnameTextFieldHeader)
        centreStackView.addArrangedSubview(surnameTextField)
        centreStackView.addArrangedSubview(nameTextFieldHeader)
        centreStackView.addArrangedSubview(nameTextField)
        centreStackView.addArrangedSubview(lastnameTextFieldHeader)
        centreStackView.addArrangedSubview(lastnameTextField)
        centreStackView.addArrangedSubview(emailTextFieldHeader)
        centreStackView.addArrangedSubview(emailTextField)
        centreStackView.addArrangedSubview(birthdayTextFieldHeader)
        centreStackView.addArrangedSubview(birthdateTextField)
        centreStackView.addArrangedSubview(passwordTextFieldHeader)
        centreStackView.addArrangedSubview(passwordTextField)
        centreStackView.addArrangedSubview(confirmPasswordTextFieldHeader)
        centreStackView.addArrangedSubview(confirmPasswordTextField)
    }
    
    
    @objc
    private func doneDateTapped() {
        birthdateTextField.text = dateFormatter.string(from: datePicker.date)
        birthdateTextField.resignFirstResponder()
    }
    
    @objc
    private func registrationButtonTapped() {
        onRegisterTap?()
    }
        
}
