# Load Matching System - Backend API

A smart logistics platform that automatically matches shipping loads with the best available drivers based on distance,
capacity, budget, and experience. Built with Django REST Framework, PostgreSQL, and Redis caching.

## 🚀 Features

- **Smart Load Matching**: AI-powered algorithm that scores and ranks drivers based on multiple criteria
- **Real-time Driver Availability**: Instant status updates with automatic cache invalidation
- **Performance Optimized**: Redis caching with 10-minute match result caching
- **Bulk Operations**: Admin tools for managing multiple drivers simultaneously
- **Comprehensive API**: RESTful endpoints with detailed documentation
- **Advanced Filtering**: Efficient database queries with proper indexing
- **Load Suggestions**: Automatic suitable load recommendations for available drivers

## 🏗️ Technology Stack

- **Backend**: Django 5.1+ with Django REST Framework
- **Database**: PostgreSQL 13+
- **Cache**: Redis 6+
- **Authentication**: JWT Token-based authentication
- **Python**: 3.9+

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.9 or higher
- PostgreSQL 13 or higher
- Redis 6 or higher
- pip (Python package manager)
- virtualenv (recommended)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/XusanDev07/logistics-load-matching-api.git
cd logistics-load-matching-api
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_NAME=load_matching_db
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 5. Database Setup

```bash
# Create PostgreSQL database
createdb load_matching_db

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 6. Start Redis Server

```bash
# On macOS with Homebrew
brew services start redis

# On Ubuntu/Debian
sudo systemctl start redis-server

# On Windows (if using WSL)
sudo service redis-server start

# Verify Redis is running
redis-cli ping
# Should return: PONG
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

## ℹ️ If you want to use the pre-filled data, then use this command.
```bash
python manage.py loaddata fixtures/db.json
```
The API will be available at `http://localhost:8000`

## 🧮 Matching Algorithm

The system uses a weighted scoring algorithm to rank drivers:

### Scoring Criteria

- **Distance Score (35%)**: Proximity between driver's home city and pickup location
    - Same city: 100 points
    - Nearby cities: 75 points
    - Regional: 50 points
    - Long distance: 25 points

- **Capacity Match (30%)**: How well the load utilizes truck capacity
    - 80-100% utilization: 100 points
    - 60-79% utilization: 75 points
    - 40-59% utilization: 50 points
    - 20-39% utilization: 25 points

- **Budget Compatibility (25%)**: Driver rate vs. load budget
    - Within budget with efficiency bonus
    - Over budget: 0 points

- **Experience Bonus (10%)**: Additional points for experienced drivers
    - 5+ years: 20 bonus points
    - 3-4 years: 10 bonus points
    - 1-2 years: 5 bonus points

### Business Rules

- Driver must be available
- Truck capacity must accommodate load weight + 10% safety margin
- Driver's rate must fit within load budget
- Returns top 10 matches ordered by total score

## 🔧 Configuration

### City Distance Configuration

The system includes predefined city relationships for distance calculations:

```python
CITY_DISTANCES = {
    'New York': {
        'nearby': ['Philadelphia', 'Newark', 'Jersey City'],
        'regional': ['Boston', 'Washington DC', 'Baltimore']
    },
    'Los Angeles': {
        'nearby': ['San Diego', 'Long Beach', 'Anaheim'],
        'regional': ['San Francisco', 'Las Vegas', 'Phoenix']
    },
    # Add more cities as needed
}
```

### Cache Settings

- **Match Results**: Cached for 10 minutes
- **Driver Availability**: Cached for 1 hour
- **Travel Time Estimates**: Cached for 1 hour
- **Automatic Invalidation**: When driver availability changes

## 📈 Performance Optimization

### Database Indexes

Key indexes for optimal performance:

```sql
-- Driver queries
CREATE INDEX idx_driver_availability ON drivers_driver (is_available);
CREATE INDEX idx_driver_capacity ON drivers_driver (truck_capacity_kg);
CREATE INDEX idx_driver_city ON drivers_driver (home_city);

-- Load queries  
CREATE INDEX idx_load_status ON loads_load (status);
CREATE INDEX idx_load_pickup_date ON loads_load (pickup_date);
CREATE INDEX idx_load_cities ON loads_load (pickup_city, delivery_city);
```

### Caching Strategy

- **L1 - Application Cache**: Redis with structured keys
- **L2 - Database**: Query optimization with select_related/prefetch_related
- **L3 - CDN**: For static assets (future enhancement)

### Query Optimization

```python
# Optimized driver query
drivers = Driver.objects.select_related('user').filter(
    is_available=True,
    truck_capacity_kg__gte=load.weight_kg * 1.1
).prefetch_related('user')
```

## 🔒 Security

### Authentication

Uses JWT (JSON Web Tokens) for secure API access:

```python
# Include in request headers
Authorization: Bearer
eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Data Validation

- Input sanitization on all endpoints
- Type checking for critical fields
- Business rule validation (capacity, budget, dates)

## 🐳 Docker Deployment (Optional)

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    environment:
      - DEBUG=False
      
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: load_matching_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data/
      
  redis:
    image: redis:6-alpine
    
volumes:
  postgres_data:
```

## 📖 API Documentation

### Development Guidelines

- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use meaningful commit messages
- Add logging for important operations

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Xusan Khalil** - *Initial work* - [XusanDev07](https://github.com/XusanDev07)

## 🙏 Acknowledgments

- Django REST Framework team for excellent documentation
- Redis team for high-performance caching
- PostgreSQL community for robust database engine
- Open source contributors who made this project possible

## 📞 Support

- **Documentation**: [Project Wiki](https://github.com/XusanDev07/logistics-load-matching-api/wiki)
- **Issues**: [GitHub Issues](https://github.com/XusanDev07/logistics-load-matching-api/issues)
- **Discussions**: [GitHub Discussions](https://github.com/XusanDev07/logistics-load-matching-api/discussions)

---

⭐ **Star this repository if it helped you!**