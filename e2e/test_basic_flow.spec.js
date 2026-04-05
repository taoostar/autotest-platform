import { test, expect } from '@playwright/test';

const BASE_URL = 'https://localhost';
const API_URL = 'https://localhost/api/v1';

// Test suite for basic flows
test.describe('AutoTest Platform E2E Tests', () => {
  test.beforeAll(async ({ browser }) => {
    // 确保后端服务运行
    try {
      const response = await fetch(`${API_URL}/health`);
      if (!response.ok) {
        console.log('警告: 后端服务可能未运行');
      }
    } catch (e) {
      console.log('警告: 无法连接到后端服务:', e.message);
    }
  });

  test('登录页面加载', async ({ page }) => {
    await page.goto(BASE_URL);

    // 应该重定向到登录页
    await expect(page).toHaveURL(/login/);

    // 检查登录表单元素
    await expect(page.locator('input[type="text"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('登录流程', async ({ page }) => {
    await page.goto(BASE_URL);

    // 填写登录表单
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');

    // 点击登录按钮
    await page.click('button[type="submit"]');

    // 等待跳转到首页
    await page.waitForURL(/((?!login).)*$/, { timeout: 10000 });

    // 检查是否显示首页内容
    await expect(page.locator('text=首页')).toBeVisible({ timeout: 5000 });
  });

  test('导航菜单功能', async ({ page }) => {
    // 先登录
    await page.goto(BASE_URL);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/((?!login).)*$/, { timeout: 10000 });

    // 检查侧边栏菜单
    await expect(page.locator('text=测试用例')).toBeVisible();
    await expect(page.locator('text=测试计划')).toBeVisible();
    await expect(page.locator('text=测试任务')).toBeVisible();
    await expect(page.locator('text=Agent管理')).toBeVisible();
    await expect(page.locator('text=报告中心')).toBeVisible();
  });

  test('测试计划页面加载', async ({ page }) => {
    // 先登录
    await page.goto(BASE_URL);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/((?!login).)*$/, { timeout: 10000 });

    // 导航到测试计划
    await page.click('text=测试计划');
    await page.waitForURL(/plans/);

    // 检查页面内容
    await expect(page.locator('text=测试计划')).toBeVisible();
    await expect(page.locator('text=选择项目')).toBeVisible();
    await expect(page.locator('text=新建计划')).toBeVisible();
  });

  test('测试用例页面加载', async ({ page }) => {
    // 先登录
    await page.goto(BASE_URL);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/((?!login).)*$/, { timeout: 10000 });

    // 导航到测试用例
    await page.click('text=测试用例');
    await page.waitForURL(/cases/);

    // 检查页面内容
    await expect(page.locator('text=测试用例')).toBeVisible();
    await expect(page.locator('text=选择项目')).toBeVisible();
  });

  test('测试任务页面加载', async ({ page }) => {
    // 先登录
    await page.goto(BASE_URL);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/((?!login).)*$/, { timeout: 10000 });

    // 导航到测试任务
    await page.click('text=测试任务');
    await page.waitForURL(/tasks/);

    // 检查页面内容
    await expect(page.locator('text=测试任务')).toBeVisible();
    await expect(page.locator('text=状态筛选')).toBeVisible();
  });

  test('Agent管理页面加载', async ({ page }) => {
    // 先登录
    await page.goto(BASE_URL);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/((?!login).)*$/, { timeout: 10000 });

    // 导航到Agent管理
    await page.click('text=Agent管理');
    await page.waitForURL(/agents/);

    // 检查页面内容
    await expect(page.locator('text=Agent管理')).toBeVisible();
  });

  test('报告中心页面加载', async ({ page }) => {
    // 先登录
    await page.goto(BASE_URL);
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL(/((?!login).)*$/, { timeout: 10000 });

    // 导航到报告中心
    await page.click('text=报告中心');
    await page.waitForURL(/reports/);

    // 检查页面内容
    await expect(page.locator('text=报告中心')).toBeVisible();
    await expect(page.locator('text=今日成功')).toBeVisible();
    await expect(page.locator('text=今日失败')).toBeVisible();
  });
});