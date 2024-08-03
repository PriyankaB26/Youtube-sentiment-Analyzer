const express = require('express');
const bodyParser = require('body-parser');
const mysql = require('mysql');

const app = express();
const port = 3000;

// Middleware
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// MySQL connection
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root', 
  password: 'root', 
  database: 'login_reg_db'
});

db.connect(err => {
  if (err) {
    console.error('Database connection failed:', err.stack);
    return;
  }
  console.log('Connected to MySQL database');
});

// Routes
app.post('/register', (req, res) => {
  const { username, youtubeID, email, password } = req.body;
  const sql = 'INSERT INTO users (username, youtubeID, email, password) VALUES (?, ?, ?, ?)';
  db.query(sql, [username, youtubeID, email, password], (err, result) => {
    if (err) {
      return res.status(500).send(err);
    }
    res.status(200).send('User registered successfully');
  });
});

app.post('/login', (req, res) => {
  const { youtubeID, password } = req.body;
  const sql = 'SELECT * FROM users WHERE youtubeID = ? AND password = ?';
  db.query(sql, [youtubeID, password], (err, results) => {
    if (err) {
      return res.status(500).send(err);
    }
    if (results.length > 0) {
      res.status(200).send('Login successful');
    } else {
      res.status(401).send('Invalid credentials');
    }
  });
});

// Start server
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});
