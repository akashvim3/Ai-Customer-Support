# AI Customer Support Platform (SaaS)

A powerful multi-tenant AI-powered customer support platform built with Django, featuring intelligent chatbots, automated ticket classification, and real-time sentiment analytics.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/django-5.0+-green.svg)

## 🚀 Features

- **Multi-Tenant Architecture**: Isolated data for each organization using django-tenants
- **AI-Powered Chatbot**: Natural language processing with OpenAI and LangChain
- **Sentiment Analysis**: Real-time emotion detection using transformers and ensemble methods
- **Automatic Ticket Classification**: BERT-based categorization and priority assignment
- **Real-Time Analytics**: Comprehensive dashboards with Chart.js visualizations
- **WebSocket Support**: Live chat with Channels and Redis
- **RESTful API**: Complete API with JWT authentication and Swagger documentation
- **Modern UI**: Responsive design with Bootstrap 5 and custom CSS
- **Role-Based Access Control**: Owner, Admin, Agent, and Viewer roles

## 📋 Requirements

- Python 3.11+
- PostgresSQL 14+
- Redis 6+
- Node.js 16+ (for frontend assets)

## 🛠️ Installation

### 1. Clone the Repository

     git clone https://github.com/akashvim3/ai-customer-support.git
     cd ai-customer-support

### 2. Create Virtual Environment

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

### 3. Install Dependencies

    pip install -r requirements.txt

### 4. Set Up Environment Variables

    cp .env.example .env
    Edit .env with your configuration

### 5. Create PostgresSQL Database

    createdb ai_support_db

### 6. Run Migrations

    python manage.py migrate_schemas
    python manage.py createsuperuser

### 7. Create Public Tenant

    python manage.py shell

Create public tenanted = Tenant(schema_name='public', name='Public')
tenant.save()Create domaindomain = Domain()
domain.domain = 'localhost'
domain.tenant = tenant
domain.is_primary = True
domain.save()

### 8. Collect Static Files

    python manage.py collectstatic --noinput

### 9. Start Development Server

    python manage.py runserver

### 10. Start Celery Worker (In separate terminal)

    celery -A config worker --loglevel=info

### 11. Start Celery Beat (In separate terminal)

    celery -A config beat --loglevel=info

## 🎯 Usage

### Access the Application

- **Homepage**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **API Documentation**: http://localhost:8000/api/docs
- **Dashboard**: http://localhost:8000/dashboard

### Create a Tenant

1. Register at http://localhost:8000/register
2. Complete the registration form
3. Access your tenant dashboard

### API Endpoints

POST /api/tenants/register/register/          # Register new tenant
POST /api/auth/token/                          # Get JWT token
GET  /api/tickets/                             # List tickets
POST /api/chatbot/chat/message/                # Send chat message
GET  /api/analytics/overview/                  # Get analytics

## 📚 Project Structure

    ai_customer_support/
    ├── config/              # Django settings
    ├── tenants/             # Multi-tenant management
    ├── chatbot/             # AI chatbot engine
    ├── tickets/             # Ticket management
    ├── analytics/           # Analytics and reporting
    ├── dashboard/           # Dashboard views
    ├── ml_models/           # ML model storage
    ├── templates/           # HTML templates
    ├── static/              # CSS, JS, images
    └── media/               # User uploads

## 🔧 Configuration

### AI Models

Configure AI models in `config/settings.py`:
OPENAI_API_KEY = 'your-api-key'
SENTIMENT_MODEL = 'cardiffnlp/twitter-roberta-base-sentiment'
TICKET_CLASSIFIER_MODEL = 'bert-base-uncased'

### Celery Tasks

Tasks are configured for:
- Automated ticket assignment
- Sentiment analysis
- Email notifications
- Report generation

## 🧪 Testing

    pytest

## 📦 Deployment

### Heroku

heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
git push heroku main
heroku run python manage.py migrate_schemas

### Docker

    docker-compose up --build

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Your Name - [@akashvimal](https://twitter.com/akashvimal)

## 🙏 Acknowledgments

- Django & DRF community
- Hugging Face for transformer models
- OpenAI for GPT models
- Bootstrap team

## 📞 Support

For support, email support@aisupport.com or join our Slack channel.