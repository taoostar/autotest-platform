import { test, expect, chromium } from '@playwright/test';

const BASE_URL = 'https://localhost';
const API_URL = 'https://localhost/api/v1';

test.describe('AutoTest Platform - Create Test Data via UI', () => {
  let apiContext;
  let token = '';

  test.beforeAll(async ({ playwright }) => {
    // Create API context with ignore HTTPS errors
    apiContext = await playwright.request.newContext({
      ignoreHTTPSErrors: true
    });

    // Login via API
    const loginResponse = await apiContext.post(`${API_URL}/auth/login`, {
      data: { username: 'admin', password: 'admin123' }
    });
    const loginData = await loginResponse.json();
    token = loginData.access_token;
    console.log('Logged in via API, token obtained');
  });

  test.afterAll(async () => {
    await apiContext.dispose();
  });

  test('Login via UI', async ({ page }) => {
    await page.goto(BASE_URL);

    // Wait for redirect to login
    await expect(page).toHaveURL(/login/);

    // Fill login form
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');

    // Submit
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL(/((?!login).)*$/, { timeout: 10000 });

    // Verify logged in
    await expect(page.locator('text=首页')).toBeVisible({ timeout: 5000 });
    console.log('Logged in via UI');
  });

  test('Create 5 Modules', async () => {
    for (let i = 1; i <= 5; i++) {
      await apiContext.post(`${API_URL}/projects/1/modules`, {
        data: { name: `Module ${i}`, description: `Test Module ${i}` },
        headers: { 'Authorization': `Bearer ${token}` }
      });
    }
    console.log('Created 5 modules');
  });

  test('Create 50 Test Cases', async () => {
    for (let i = 1; i <= 50; i++) {
      const moduleId = 2 + Math.floor((i - 1) / 10);
      const scriptContent = `def test_case_${i}():
    assert 1 + 1 == 2, "Test ${i} should pass"
    print("Test case ${i} passed")

test_case_${i}()`;

      await apiContext.post(`${API_URL}/modules/${moduleId}/cases`, {
        data: {
          name: `UI Test Case ${i}`,
          description: `Automated test case ${i}`,
          script_type: 'python',
          priority: 1 + (i - 1) % 5,
          timeout: 60,
          code: scriptContent
        },
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (i % 10 === 0) {
        console.log(`Created ${i} test cases...`);
      }
    }
    console.log('Created 50 test cases');
  });

  test('Create 10 Test Plans', async () => {
    for (let i = 1; i <= 10; i++) {
      await apiContext.post(`${API_URL}/projects/1/plans`, {
        data: {
          name: `UI Test Plan ${i}`,
          description: `Automated test plan ${i}`
        },
        headers: { 'Authorization': `Bearer ${token}` }
      });
      console.log(`Created plan ${i}`);
    }
  });

  test('Add Cases to Plans', async () => {
    // Add 5 cases to each of plans 12-21 (newly created plans)
    for (let planIdx = 0; planIdx < 10; planIdx++) {
      const planId = 12 + planIdx; // Plans 12-21
      const startCase = planIdx * 5 + 1;
      const caseIds = Array.from({ length: 5 }, (_, idx) => startCase + idx);

      await apiContext.put(`${API_URL}/plans/${planId}/cases`, {
        data: { case_ids: caseIds },
        headers: { 'Authorization': `Bearer ${token}` }
      });

      console.log(`Added cases to plan ${planId}`);
    }
  });

  test('Create 10 Test Tasks', async () => {
    for (let i = 1; i <= 10; i++) {
      await apiContext.post(`${API_URL}/tasks`, {
        data: {
          plan_id: 11 + i, // plans 12-21
          trigger_type: 'manual'
        },
        headers: { 'Authorization': `Bearer ${token}` }
      });
      console.log(`Created task ${i} for plan ${11 + i}`);
    }
  });

  test('Dispatch 8 Tasks via API', async () => {
    // Update agent to online first
    await apiContext.post(`${API_URL}/agents/1`, {
      data: { status: 'online' },
      headers: { 'Authorization': `Bearer ${token}` }
    });

    // Dispatch tasks 11-18 (the newly created tasks)
    for (let taskId = 11; taskId <= 18; taskId++) {
      const response = await apiContext.post(`${API_URL}/tasks/${taskId}/dispatch`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok()) {
        console.log(`Dispatched task ${taskId}`);
      } else {
        const error = await response.text();
        console.log(`Task ${taskId} dispatch failed: ${error.substring(0, 100)}`);
      }
    }
  });

  test('Verify via UI', async ({ page }) => {
    // Navigate to tasks page
    await page.click('text=测试任务');
    await page.waitForTimeout(2000);

    const taskRows = await page.locator('table tbody tr').count();
    console.log(`Found ${taskRows} task rows in table`);
  });
});