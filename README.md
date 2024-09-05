**Greetings!** This is a short test application developed to manage books for a community library. This project was created for Inforce IT company.     
       
The application allows for the creation of two types of users: library staff and member. Additionally, an admin can be created with access to a basic admin panel inherited from Django. After registration, it is mandatory to confirm the email by clicking the link provided in the email message. Post-registration, users need to log in to access the library functionalities. Users also have the option to log out. Only library staff can delete users; they can remove themselves or a library client without outstanding debts, but not other staff members.     
      
The functionality includes allowing users to borrow books (note that if a user has borrowed a book, they cannot borrow another copy of the same book), return books, view all books, or look up a specific book. Library staff can also view all books or a single book, perform CRUD operations on books, and access information about visitors and their borrowed books.     
      
It is worth noting that when a user borrows or returns a book, an email notification is sent both to the user and the system.       
    
**Tech Overview**     
- Backend Only (UI is not included)    
- REST Architecture    
- Tech Stack: Django Rest Framework (DRF), PostgreSQL, Docker (docker-compose), Celery (for background tasks such as sending email notifications)    
- Code Coverage: All code is covered by unit tests    
- Documentation: README.md provides detailed instructions on how to run the system    
- Code Quality: Code linting is implemented using flake8 and isort    
- Documentation: Docstrings have been added throughout the code    
- Security: Environment variables are used for sensitive data (e.g., email server configuration, database credentials)     
- Setup: The system can be run using docker-compose, with all necessary steps and information included in the README
      
**WARNING!**       
The `.env` file is **NOT** pushed to GitHub. This file must include the following items:      
- `SECRET_KEY`='django-SECRET_KEY-example'     
- `DEBUG`=True/False     
- `DB_HOST`=dbexamlpe     
- `DB_NAME`=devdbexamlpe     
- `DB_USER`=devuserexamlpe     
- `DB_PASS`=dbpassexamlpe     
- `POSTGRES_DB`=devdbexamlpe     
- `POSTGRES_USER`=devuserexamlpe     
- `POSTGRES_PASSWORD`=dbpassexamlpe         
- `EMAIL_HOST`=smtp.gmail.com    
- `EMAIL_HOST_USER`=exampleemail@gmail.com     
- `EMAIL_HOST_PASSWORD`=examplepassword     
- `EMAIL_PORT`=587     
- `EMAIL_USE_TLS`=True/False     
- `CELERY_BROKER_URL`=redis://redis:1111/0     
- `CELERY_RESULT_BACKEND`=redis://redis:1111/0     
- `CELERY_TASK_ALWAYS_EAGER`=True/False      
- `CELERY_EAGER_PROPAGATES_EXCEPTIONS`=True/False      
- `PASSWORD_LENGTH`=int_number     
**WARNING!**              
          
1)Authentication    
    
**localhost:8321/api/register/(POST)** - Registers a user (user_type: LIBRARY_USER = 0, VISITOR_USER = 1). You need to confirm your email by clicking the link in the confirmation email.    
Request Body:    
{     
    "name": "nameexample",    
    "email": "emailexample@gmail.com",    
    "password": "Example1234",    
    "user_type": 0    
}    
    
**localhost:8321/api/login/(POST)** - After clicking the special link, the is_active field will be set to true, and you can log in.     
Request Body:    
{    
    "email": "emailexample@gmail.com",    
    "password": "Example1234",    
} 
    
**localhost:8321/api/logout/(POST)** - You need to include the following in the request headers:     
Key: Authorization      
Value: Bearer {jwt token}    
     
**localhost:8321/api/delete/(DELETE)** - You need to include the following in the request headers:    
Key: Authorization    
Value: Bearer {jwt token}       
Only LIBRARY_USER can delete their own account.       
     
**localhost:8321/api/delete-visitor/{id}/(DELETE)** - You need to include the following in the request headers:    
Key: Authorization    
Value: Bearer {jwt token}       
Only LIBRARY_USER can delete a VISITOR_USER, provided that the VISITOR_USER has returned all borrowed books. LIBRARY_USER can not delete another LIBRARY_USER.     
     
**localhost:8321/api/activate/{id}/(GET)** - This api will be in special letter, you need to click him to activate user.   
     
For all next sections you need to include the following in the request headers:   
Key: Authorization    
Value: Bearer {jwt token}  
     
2)Books   
    
**localhost:8321/api/books/(GET)** - List all books.    
         
**localhost:8321/api/books/(POST)** - Create a new book. Only accessible by users with LIBRARY_USER type.        
{    
    "title": "example title book",    
    "author": "example author book",    
    "total_copies": "5"    
}    
**localhost:8321/api/book/{id}/(GET)** - Retrieve a specific book by ID.    
    
**localhost:8321/api/book/{id}/(PATCH)** - Update a specific book by ID. Only accessible by users with LIBRARY_USER type.
    
**localhost:8321/api/book/{id}/(DELETE)** - Delete a specific book by ID. Only accessible by users with LIBRARY_USER type.
    
3)Borrow    
    
**localhost:8321/api/borrow/{id}/(POST)** - Borrow a book. Only visitors can borrow books. Sends notification emails to the user and library staff.    
    
**localhost:8321/api/return/{id}/(POST)** - Return a borrowed book. Only visitors can return books. Sends notification emails to the user and library staff.    
    
**localhost:8321/api/user-borrowed-books/{id}/(GET)** - Retrieve all borrowed books for a specific user. Only library staff can access this.    
    
**localhost:8321/api/my-borrowed-books/(GET)** - Retrieve all borrowed books for the authenticated user.    
    
4)Admin    
    
**http://127.0.0.1:8321/admin/(GET)** - Access the admin panel.    
