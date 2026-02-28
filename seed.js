// Local JSON DB Seed
const User = require('./models/User');
const dotenv = require('dotenv');

dotenv.config();

console.log('Seeding Local JSON Database...');
// No connection needed for JSON DB


const seedUsers = async () => {
    try {
        // Clear existing users? Maybe not, just check if they exist.
        // Let's force create specific demo users.

        const demoInstructor = {
            name: 'Demo Instructor',
            email: 'instructor@demo.com',
            password: 'password123',
            role: 'instructor'
        };

        const demoLearner = {
            name: 'Demo Learner',
            email: 'learner@demo.com',
            password: 'password123',
            role: 'learner'
        };

        // Check and create Instructor
        const instructorExists = await User.findOne({ email: demoInstructor.email });
        if (!instructorExists) {
            await User.create(demoInstructor); // Pre-save hook will hash password
            console.log('Demo Instructor created');
        } else {
            console.log('Demo Instructor already exists');
        }

        // Check and create Learner
        const learnerExists = await User.findOne({ email: demoLearner.email });
        if (!learnerExists) {
            await User.create(demoLearner);
            console.log('Demo Learner created');
        } else {
            console.log('Demo Learner already exists');
        }

        process.exit();
    } catch (error) {
        console.error('Error seeding data:', error);
        process.exit(1);
    }
};

seedUsers();
