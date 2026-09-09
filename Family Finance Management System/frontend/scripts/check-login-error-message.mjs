import { readFile } from 'node:fs/promises'

const source = await readFile(new URL('../src/pages/LoginPage.tsx', import.meta.url), 'utf8')

if (!source.includes('用户名或密码错误')) {
  throw new Error('登录页没有展示错误密码提示')
}

if (!source.includes('catch')) {
  throw new Error('登录提交没有处理认证失败')
}

console.log('登录错误提示回归检查通过')
