# Recollination Project

This project is a Flask application that connects to a MongoDB database to manage user contacts. It allows for the identification and linking of primary and secondary contacts based on email and phone number.



https://github.com/user-attachments/assets/d35cdba8-91db-467f-bd43-4ccedfd43aff



## Project Structure

```
collinatiol
├── templates
│   └── index.html
├── app.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the repository:**

   ```
   git clone <repository-url>
   cd collinatiol
   ```

2. **Create a virtual environment:**

   ```
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install the required packages:**

   ```
   pip install -r requirements.txt
   ```

5. **Run the application:**

   ```
   python app.py
   ```

6. **Access the application:**
   Open your web browser and go to `http://127.0.0.1:5000/`.

## Usage

- The application serves an HTML page that allows users to input their email and phone number.
- Upon submission, the application will identify or create a primary contact and link any secondary contacts as necessary.
- The application utilizes a MongoDB database to store and manage contact information.

## License

This project is licensed under the MIT License.
