# 🎾 Tennis Training Registration System

A comprehensive tennis training registration and planning system built with Streamlit. This system provides both public registration capabilities and administrative management tools for tennis clubs.

## 🌟 Features

### 🔓 Public Registration (Port 8502)
- **Multilingual Support**: Full Dutch/English interface
- **KNLTB Skill Level Integration**: Official KNLTB skill levels (1-9) with detailed descriptions
- **Smart Training Selection**: Multiple preference system with validation
- **Permission System**: Automatic validation for higher-level training requests
- **Professional UI**: Dark theme with modern, responsive design
- **Duplicate Prevention**: Phone-based duplicate detection and replacement
- **Registration Status Control**: Can be opened/closed by administrators

### 🔐 Admin Dashboard (Port 8501)
- **Secure Authentication**: Login system with session management
- **Registration Management**: View and manage all training registrations
- **Round Planning System**: Automated and manual training assignment tools
- **Period Management**: Control registration periods and system status
- **Training Management**: Configure available trainings and schedules
- **Upload System**: Batch import of registration data
- **Login History**: Security monitoring and access logs

### 🎯 Smart Planning Features
- **Automated Assignment**: Algorithm-based training assignments
- **Preference Matching**: Respects user training preferences
- **Level Validation**: Ensures appropriate skill level matching
- **Capacity Management**: Handles training group size limits
- **Manual Override**: Admin can manually adjust assignments

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/training_inplanner.git
   cd training_inplanner
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the applications**
   
   **Public Registration** (in one terminal):
   ```bash
   streamlit run public_registration.py --server.port 8502
   ```
   
   **Admin Dashboard** (in another terminal):
   ```bash
   streamlit run app.py --server.port 8501
   ```

4. **Access the applications**
   - Public Registration: http://localhost:8502
   - Admin Dashboard: http://localhost:8501

## 📱 Usage

### For Players (Public Registration)

1. **Navigate to** http://localhost:8502
2. **Select your language** (Dutch/English)
3. **Fill in personal details**:
   - Name and phone number
   - KNLTB skill level (1-9)
   - Permission checkbox if needed
4. **Choose training preferences**:
   - Select frequency (1x, 2x, or 3x per week)
   - Set preferences for each training slot
5. **Submit registration**

### For Administrators

1. **Navigate to** http://localhost:8501
2. **Login** with admin credentials
3. **Available functions**:
   - **📋 Aanmeldingen**: View all registrations
   - **🎯 Ronde Planning**: Create training assignments
   - **📅 Periode Beheer**: Manage registration periods
   - **📅 Trainingsbeheer**: Configure available trainings
   - **🔍 Login Geschiedenis**: Monitor system access

## 🏗️ System Architecture

```
training_inplanner/
├── app.py                          # Admin dashboard main app
├── public_registration.py          # Public registration main app
├── components/                     # Reusable components
│   ├── aanmeldingen.py            # Registration management
│   ├── auth.py                    # Authentication system
│   ├── beheer.py                  # Training management
│   ├── periode_beheer.py          # Period management
│   ├── registration_form_simple.py # Modern registration form
│   ├── ronde_planning.py          # Planning algorithms
│   └── upload.py                  # Data import tools
├── data/                          # Data storage
│   ├── training1_inschrijvingen.csv
│   ├── training2_inschrijvingen.csv
│   ├── training3_inschrijvingen.csv
│   ├── trainings.csv              # Available trainings
│   ├── periode_status.json        # Registration status
│   └── auth_log.json             # Security logs
├── utils/
│   └── logic.py                   # Core business logic
└── archive/                       # Historical data
```

## 🎾 KNLTB Skill Level System

The system uses the official KNLTB (Royal Dutch Tennis Association) skill level classification:

- **Level 1-2**: 🏆 National/International level (ATP/WTA players)
- **Level 3-4**: 🎾 Regional top / Club champions
- **Level 5-6**: ⚽ Advanced club level / Active competitive players
- **Level 7-8**: 🌱 Advanced beginners / Recreational players
- **Level 9**: 🆕 Absolute beginners

## 🔧 Configuration

### Admin Credentials
Default admin access can be configured in the authentication system. The system supports session-based login with security logging.

### Training Configuration
Trainings are configured via the admin dashboard or by editing `data/trainings.csv`:
```csv
Dag,Tijd,MinNiveau,MaxNiveau,Trainer
Maandag,19:00,6,9,Trainer Name
Dinsdag,20:00,4,7,Another Trainer
```

### Registration Periods
Control registration availability through the admin dashboard's Period Management section.

## 🌐 Multilingual Support

The system fully supports:
- 🇳🇱 **Dutch** (Nederlands)
- 🇬🇧 **English**

All user-facing text, validation messages, and system notifications are translated.

## 📊 Data Management

### Registration Data
- Separate CSV files for each training session
- Phone-based duplicate prevention
- Timestamped entries with full audit trail

### Planning Data
- Automated assignment algorithms
- Manual override capabilities
- Historical planning data retention

## 🔒 Security Features

- Session-based authentication
- Login attempt logging
- Admin access control
- Secure data handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the existing [Issues](https://github.com/yourusername/training_inplanner/issues)
2. Create a new issue with detailed information
3. Include steps to reproduce any bugs

## 🎯 Roadmap

- [ ] Email notification system
- [ ] Mobile app version
- [ ] Advanced reporting features
- [ ] Integration with club management systems
- [ ] Payment processing integration

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Uses [Pandas](https://pandas.pydata.org/) for data management
- KNLTB skill level system integration
- Modern UI/UX design principles

---

**Made with ❤️ for tennis clubs everywhere** 🎾 