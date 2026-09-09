import { readFile } from 'node:fs/promises'

const source = await readFile(new URL('../src/pages/PersonalStatisticsPage.tsx', import.meta.url), 'utf8')

if (!source.includes("reportApi.personalSummary")) {
  throw new Error('个人统计页没有调用个人汇总接口')
}

if (!source.includes("reportApi.personalByCategory")) {
  throw new Error('个人统计页没有调用个人分类统计接口')
}

if (source.includes('useFinanceStore') || source.includes('../data/financeData')) {
  throw new Error('个人统计页仍依赖本地演示数据')
}

console.log('个人统计真实接口回归检查通过')
