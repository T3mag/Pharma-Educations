import UIKit

enum Texts {
    enum Errors {
        static let unknownError = "Что-то пошло не так, попробуйте позже"
        static let emptyString = "Поле не должно быть пустым"
        static let invalidEmail = "Некорректный email"
        static let passwordNoMatched = "Пароли не совпадают"
    }
    
    enum Login {
        static let title = "Привет, чтобы начать работу, необходимо авторизоваться"
        static let loginHeader = "Логин"
        static let loginPlaceholder = "Введите логин"
        static let passwordHeader = "Пароль"
        static let passwordPlaceholder = "Введите пароль"
        static let registrationButton = "Нет акккаунта? \n Зарегистрироваться"
        static let loginButton = "Войти"
    }
    
    enum Registration {
        static let title = "Регистрация"
        static let nameHaeader = "Имя"
        static let surnameHeader = "Фамилия"
        static let lastnameHeader = "Отчество"
        static let birthdayHeader = "Дата рождения"
        static let userStatusHeader = "Статус"
        static let emailHeader = "Электронная почта"
        static let passwordHeader = "Пароль"
        static let repeatpasswordHeader = "Проверка пароля"
        static let namePlaceholder = "Введите имя"
        static let surnamePlaceholder = "Введите фамилию"
        static let lastnamePlaceholder = "Введите отчество (при наличие)"
        static let birthdayPlaceholder = "Дата рождения"
        static let userStatusPlaceholder = "Статус"
        static let emailPlaceholder = "Введите электронную почту"
        static let passwordPlaceholder = "Введите пароль"
        static let repeatpasswordPlaceholder = "Повторите пароль"
        static let registrationButton = "Зарегистрироваться"
        static let emailPattern = #"^[A-Z0-9a-z._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"#
    }
}

