const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 8000;

// Middleware
app.use(cors());
app.use(express.json());

// Database Connection
// Database Connection
console.log('Using Local JSON Database');
require('./utils/jsonDb'); // Ensure DB is initialized
// mongoose.connect not required anymore

// Routes
const authRoutes = require('./routes/auth');
app.use('/auth', authRoutes);

const courseRoutes = require('./routes/courses');
const quizRoutes = require('./routes/quizzes');
app.use('/courses', courseRoutes);
app.use('/quizzes', quizRoutes);

app.get('/', (req, res) => {
    res.send('API is running...');
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
