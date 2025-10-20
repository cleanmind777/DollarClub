# SQLAlchemy ORM Implementation Guide

## Overview

The DollarClub Trading Platform uses **SQLAlchemy** as the primary ORM (Object-Relational Mapping) tool. This guide covers the comprehensive SQLAlchemy implementation with advanced features, best practices, and usage examples.

## 🎯 **SQLAlchemy Features Implemented**

### ✅ **Core SQLAlchemy Components**

1. **Declarative Base**: All models inherit from `Base`
2. **Engine Configuration**: Enhanced PostgreSQL engine with connection pooling
3. **Session Management**: Proper session handling with dependency injection
4. **Database Events**: Connection event listeners for database-specific settings

### ✅ **Advanced SQLAlchemy Features**

#### **Model Features**
- **Hybrid Properties**: Computed properties that work in both Python and SQL
- **Validation**: Built-in field validation using `@validates` decorator
- **Indexes**: Performance-optimized database indexes
- **Check Constraints**: Database-level data integrity constraints
- **Relationships**: Proper foreign key relationships with cascading
- **Enum Types**: Type-safe enumeration fields

#### **Query Features**
- **Class Methods**: Reusable query methods on models
- **Pagination**: Built-in pagination support
- **Complex Queries**: Advanced filtering and joining
- **Aggregation**: Statistical queries with SQL functions
- **Lazy Loading**: Optimized relationship loading

## 🏗️ **Architecture Overview**

### **Database Layer**
```
backend/app/core/database.py
├── Engine Configuration
├── Session Management
├── Connection Pooling
├── Event Listeners
└── Database Utilities
```

### **Model Layer**
```
backend/app/models/
├── user.py          # User model with authentication
├── script.py        # Script model with execution tracking
└── __init__.py      # Model exports
```

### **Service Layer**
```
backend/app/services/database_service.py
├── UserService      # User database operations
├── ScriptService    # Script database operations
└── DatabaseService  # General database utilities
```

## 📊 **Enhanced Models**

### **User Model Features**

```python
class User(Base):
    # Primary key with auto-increment
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields with validation
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), nullable=False)
    
    # Enum types for type safety
    auth_provider = Column(Enum(AuthProvider), default=AuthProvider.EMAIL)
    
    # Hybrid properties (work in Python and SQL)
    @hybrid_property
    def is_ibkr_connected(self):
        return self.ibkr_user_id is not None
    
    # Validation methods
    @validates('email')
    def validate_email(self, key, email):
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise ValueError('Invalid email format')
        return email.lower()
    
    # Class methods for common queries
    @classmethod
    def get_by_email(cls, session, email):
        return session.query(cls).filter(cls.email == email.lower()).first()
    
    # Relationships with lazy loading
    scripts = relationship("Script", back_populates="owner", cascade="all, delete-orphan", lazy="select")
```

### **Script Model Features**

```python
class Script(Base):
    # Foreign key with cascade delete
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Execution metrics with precision
    execution_time_seconds = Column(Numeric(10, 3), nullable=True)
    memory_usage_mb = Column(Numeric(10, 2), nullable=True)
    
    # Complex constraints
    __table_args__ = (
        CheckConstraint("file_size > 0", name='ck_positive_file_size'),
        CheckConstraint("execution_time_seconds >= 0", name='ck_non_negative_execution_time'),
        Index('ix_scripts_user_status', 'user_id', 'status'),
    )
    
    # Instance methods for business logic
    def start_execution(self, session):
        self.status = ScriptStatus.RUNNING
        self.started_at = func.now()
        session.commit()
    
    def complete_execution(self, session, exit_code=0, execution_time=None):
        self.status = ScriptStatus.COMPLETED
        self.completed_at = func.now()
        self.exit_code = exit_code
        if execution_time is not None:
            self.execution_time_seconds = execution_time
        session.commit()
```

## 🔧 **Database Configuration**

### **Enhanced Engine Setup**

```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before use
    pool_recycle=300,        # Recycle connections every 5 minutes
    echo=settings.DEBUG,     # Log SQL queries in debug mode
    connect_args={
        "options": "-c timezone=utc"  # Set timezone to UTC
    }
)

# Session configuration with enhanced features
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)
```

### **Connection Event Listeners**

```python
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set database-specific configurations on connection"""
    if "postgresql" in settings.DATABASE_URL:
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone TO 'UTC'")
    elif "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
```

## 🚀 **Service Layer Implementation**

### **UserService Example**

```python
class UserService:
    @staticmethod
    def create_user(session: Session, email: str, username: str, 
                   hashed_password: str = None, auth_provider: AuthProvider = AuthProvider.EMAIL) -> User:
        """Create a new user with validation"""
        user = User(
            email=email.lower(),
            username=username,
            hashed_password=hashed_password,
            auth_provider=auth_provider
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    def get_users_with_pagination(session: Session, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Get users with pagination"""
        offset = (page - 1) * per_page
        total = session.query(User).count()
        users = session.query(User).offset(offset).limit(per_page).all()
        
        return {
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
    
    @staticmethod
    def search_users(session: Session, query: str, limit: int = 20) -> List[User]:
        """Search users by email or username"""
        search_term = f"%{query.lower()}%"
        return session.query(User).filter(
            or_(
                User.email.ilike(search_term),
                User.username.ilike(search_term)
            )
        ).limit(limit).all()
```

### **ScriptService Example**

```python
class ScriptService:
    @staticmethod
    def get_script_stats(session: Session) -> Dict[str, Any]:
        """Get comprehensive script statistics"""
        total_scripts = session.query(Script).count()
        running_scripts = session.query(Script).filter(Script.status == ScriptStatus.RUNNING).count()
        
        # Total file size using SQL aggregation
        total_size = session.query(func.sum(Script.file_size)).scalar() or 0
        
        # Average execution time
        avg_execution_time = session.query(func.avg(Script.execution_time_seconds)).filter(
            Script.execution_time_seconds.isnot(None)
        ).scalar() or 0
        
        return {
            'total_scripts': total_scripts,
            'running_scripts': running_scripts,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'avg_execution_time': float(avg_execution_time) if avg_execution_time else 0
        }
```

## 📈 **Advanced Query Examples**

### **Complex Filtering**

```python
# Get users with IBKR connected and recent activity
recent_users = session.query(User).filter(
    and_(
        User.ibkr_user_id.isnot(None),
        User.last_login_at >= datetime.utcnow() - timedelta(days=7)
    )
).all()

# Get scripts by multiple criteria
complex_query = session.query(Script).filter(
    and_(
        Script.status == ScriptStatus.COMPLETED,
        Script.execution_time_seconds > 10,
        Script.created_at >= datetime.utcnow() - timedelta(days=30)
    )
).order_by(desc(Script.execution_time_seconds)).limit(10)
```

### **Aggregation Queries**

```python
# User statistics by auth provider
stats = session.query(
    User.auth_provider,
    func.count(User.id).label('user_count'),
    func.avg(func.extract('epoch', User.created_at)).label('avg_creation_time')
).group_by(User.auth_provider).all()

# Script execution statistics
execution_stats = session.query(
    Script.status,
    func.count(Script.id).label('count'),
    func.avg(Script.execution_time_seconds).label('avg_time'),
    func.sum(Script.file_size).label('total_size')
).group_by(Script.status).all()
```

### **Relationship Queries**

```python
# Get users with their script counts
users_with_counts = session.query(
    User,
    func.count(Script.id).label('script_count')
).outerjoin(Script).group_by(User.id).all()

# Get recent scripts with user information
recent_scripts_with_users = session.query(Script, User).join(
    User, Script.user_id == User.id
).filter(
    Script.created_at >= datetime.utcnow() - timedelta(days=7)
).order_by(desc(Script.created_at)).all()
```

## 🔒 **Data Integrity Features**

### **Check Constraints**

```python
# Database-level constraints
__table_args__ = (
    CheckConstraint(
        "CASE WHEN auth_provider = 'email' THEN hashed_password IS NOT NULL ELSE TRUE END",
        name='ck_email_password_required'
    ),
    CheckConstraint("file_size > 0", name='ck_positive_file_size'),
    CheckConstraint("execution_time_seconds >= 0", name='ck_non_negative_execution_time'),
)
```

### **Validation Methods**

```python
@validates('email')
def validate_email(self, key, email):
    """Validate email format at the model level"""
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        raise ValueError('Invalid email format')
    return email.lower()

@validates('file_size')
def validate_file_size(self, key, file_size):
    """Validate file size is positive"""
    if file_size is not None and file_size <= 0:
        raise ValueError('File size must be positive')
    return file_size
```

## 📊 **Performance Optimization**

### **Indexes for Query Performance**

```python
# Composite indexes for common query patterns
__table_args__ = (
    Index('ix_users_email_provider', 'email', 'auth_provider'),
    Index('ix_scripts_user_status', 'user_id', 'status'),
    Index('ix_scripts_created_at', 'created_at'),
    Index('ix_users_last_login', 'last_login_at'),
)
```

### **Lazy Loading Configuration**

```python
# Optimized relationship loading
scripts = relationship(
    "Script", 
    back_populates="owner", 
    cascade="all, delete-orphan",
    lazy="select"  # Lazy loading for better performance
)
```

### **Query Optimization**

```python
# Use joinedload for eager loading when needed
users_with_scripts = session.query(User).options(
    joinedload(User.scripts)
).filter(User.is_active == True).all()

# Use select_related for single queries
user_with_scripts = session.query(User).options(
    joinedload(User.scripts)
).filter(User.id == user_id).first()
```

## 🛠️ **Usage Examples**

### **Creating Records**

```python
# Using service layer
with get_db_session() as session:
    user = UserService.create_user(
        session=session,
        email="user@example.com",
        username="testuser",
        hashed_password=hash_password("password123")
    )
    
    script = ScriptService.create_script(
        session=session,
        user_id=user.id,
        filename="trading_strategy.py",
        original_filename="my_strategy.py",
        file_path="/path/to/script",
        file_size=1024
    )
```

### **Querying Records**

```python
# Using model class methods
with get_db_session() as session:
    # Get user by email
    user = User.get_by_email(session, "user@example.com")
    
    # Get user's scripts with pagination
    scripts_data = Script.get_by_user(session, user.id, page=1, per_page=10)
    
    # Get running scripts
    running_scripts = Script.get_running_scripts(session)
```

### **Updating Records**

```python
# Using model instance methods
with get_db_session() as session:
    script = ScriptService.get_by_id(session, script_id)
    if script:
        script.start_execution(session)
        # ... script execution logic ...
        script.complete_execution(session, exit_code=0, execution_time=45.5)
```

### **Complex Queries**

```python
# Advanced filtering and aggregation
with get_db_session() as session:
    # Get top 10 users by script count
    top_users = session.query(
        User.username,
        func.count(Script.id).label('script_count')
    ).outerjoin(Script).group_by(User.id).order_by(
        desc('script_count')
    ).limit(10).all()
    
    # Get script performance metrics
    performance_stats = session.query(
        func.avg(Script.execution_time_seconds).label('avg_time'),
        func.max(Script.execution_time_seconds).label('max_time'),
        func.min(Script.execution_time_seconds).label('min_time'),
        func.count(Script.id).label('total_scripts')
    ).filter(
        Script.status == ScriptStatus.COMPLETED
    ).first()
```

## 🚀 **Migration Management**

### **Running Migrations**

```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### **Migration Example**

```python
def upgrade() -> None:
    # Create new table with constraints
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('status', sa.Enum('active', 'inactive'), nullable=False),
    )
    
    # Add indexes
    op.create_index('ix_new_table_status', 'new_table', ['status'])
    
    # Add constraints
    op.create_check_constraint(
        'ck_positive_id',
        'new_table',
        'id > 0'
    )
```

## 📋 **Best Practices**

### **Model Design**
1. **Use Enums**: For type-safe status fields
2. **Add Validation**: Use `@validates` for data integrity
3. **Create Indexes**: For frequently queried fields
4. **Use Hybrid Properties**: For computed fields
5. **Implement Relationships**: With proper cascading

### **Query Optimization**
1. **Use Lazy Loading**: For better performance
2. **Add Pagination**: For large datasets
3. **Use Indexes**: For common query patterns
4. **Avoid N+1 Queries**: Use joinedload when needed
5. **Use Aggregation**: For statistical queries

### **Session Management**
1. **Use Context Managers**: For proper cleanup
2. **Handle Exceptions**: With proper rollback
3. **Close Sessions**: Always close database sessions
4. **Use Transactions**: For data consistency

### **Security**
1. **Validate Input**: At model and API levels
2. **Use Constraints**: For data integrity
3. **Sanitize Data**: Before database operations
4. **Use Parameterized Queries**: Avoid SQL injection

## 🔍 **Debugging and Monitoring**

### **Query Logging**

```python
# Enable SQL query logging in development
engine = create_engine(
    settings.DATABASE_URL,
    echo=True  # Log all SQL queries
)
```

### **Performance Monitoring**

```python
# Monitor query performance
import time

start_time = time.time()
results = session.query(User).filter(User.is_active == True).all()
execution_time = time.time() - start_time
logger.info(f"Query executed in {execution_time:.3f} seconds")
```

### **Database Health Checks**

```python
# Health check endpoint
@app.get("/health/database")
async def database_health():
    return DatabaseService.get_health_check(session)
```

## 🎯 **Summary**

The DollarClub Trading Platform implements a comprehensive SQLAlchemy ORM solution with:

- **Advanced Model Features**: Hybrid properties, validation, relationships
- **Performance Optimization**: Indexes, lazy loading, query optimization
- **Data Integrity**: Constraints, validation, cascading relationships
- **Service Layer**: Clean separation of concerns with reusable methods
- **Migration Management**: Alembic integration for schema evolution
- **Monitoring**: Health checks and performance monitoring

This implementation provides a robust, scalable, and maintainable database layer that supports the platform's trading functionality while ensuring data integrity and performance.
