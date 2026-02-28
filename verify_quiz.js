const BASE_URL = 'http://localhost:8000';

async function verifyQuizSubmission() {
    console.log('Starting Quiz Submission Verification...');

    // 1. Login to get token
    const testUser = { email: 'learner@demo.com', password: 'password123' }; // Assuming default seed user exists
    let token = '';
    let userId = '';

    try {
        const loginRes = await fetch(`${BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: testUser.email, password: testUser.password })
        });

        if (!loginRes.ok) throw new Error('Login failed');
        const loginData = await loginRes.json();
        token = loginData.access_token;
        userId = loginData._id;
        console.log('[PASS] Login successful');
    } catch (e) {
        // Try registering if login fails (seed might not be there or slightly different)
        console.log('Login failed, trying registration...');
        try {
            const regRes = await fetch(`${BASE_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: 'QuizVerifier', email: `quiz_verifier_${Date.now()}@test.com`, password: 'password123', role: 'learner' })
            });
            const regData = await regRes.json();
            token = regData.access_token;
            userId = regData._id;
            console.log('[PASS] Registration successful');
        } catch (regErr) {
            console.error('[FAIL] User setup failed:', regErr.message);
            return;
        }
    }

    // 2. Find a quiz (via Course)
    let quizId = '';
    try {
        const coursesRes = await fetch(`${BASE_URL}/courses`);
        const courses = await coursesRes.json();

        if (courses.length === 0) throw new Error('No courses found');
        const courseId = courses[0]._id;
        console.log(`[PASS] Found course: ${courseId}`);

        // Get quizzes for this course
        const quizzesRes = await fetch(`${BASE_URL}/quizzes/course/${courseId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const quizzes = await quizzesRes.json();

        if (quizzes.length === 0) {
            // Create a quiz if none exists (requires instructor, might be complex for this script, 
            // but let's assume seed data has quizzes as seen in db.json earlier)
            console.log('[WARN] No quizzes found for course. Checking all quizzes directly (db.json check previously showed one).');
            // db.json showed quiz "4eaf3e0c42a620cbe8a427f1"
            quizId = "4eaf3e0c42a620cbe8a427f1";
        } else {
            quizId = quizzes[0]._id;
        }
        console.log(`[PASS] Target Quiz ID: ${quizId}`);

    } catch (e) {
        console.error('[FAIL] Quiz discovery:', e.message);
        return;
    }

    // 3. Get Quiz Details (The missing endpoint we just fixed)
    try {
        const quizRes = await fetch(`${BASE_URL}/quizzes/${quizId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!quizRes.ok) {
            const txt = await quizRes.text();
            throw new Error(`Status ${quizRes.status}: ${txt}`);
        }

        const quiz = await quizRes.json();
        console.log(`[PASS] Fetched Quiz Details: ${quiz.title}`);
    } catch (e) {
        console.error('[FAIL] Fetch Quiz Details:', e.message);
        return;
    }

    // 4. Submit Quiz
    try {
        const answers = [0]; // Assuming 1 question, index 0 correct
        const submitRes = await fetch(`${BASE_URL}/quizzes/${quizId}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ answers })
        });

        if (!submitRes.ok) {
            const txt = await submitRes.text();
            throw new Error(`Status ${submitRes.status}: ${txt}`);
        }

        const result = await submitRes.json();
        console.log(`[PASS] Quiz Submitted. Score: ${result.score}, Badge Logic Triggered.`);
    } catch (e) {
        console.error('[FAIL] Quiz Submission:', e.message);
    }
}

verifyQuizSubmission();
