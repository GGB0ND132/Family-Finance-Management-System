import { Button, Space } from 'antd'
import { useSearchParams } from 'react-router-dom'

/** 统一首页范围切换，状态写入 URL，刷新后仍保留当前视图。 */
export function HomeScopeToggle() {
  const [params, setParams] = useSearchParams()
  const family = params.get('scope') === 'family'
  const change = (scope: 'personal' | 'family') => {
    const next = new URLSearchParams(params)
    next.set('scope', scope)
    setParams(next)
  }
  return <Space.Compact aria-label="首页范围">
    <Button type={!family ? 'primary' : 'default'} onClick={() => change('personal')}>个人首页</Button>
    <Button type={family ? 'primary' : 'default'} onClick={() => change('family')}>家庭首页</Button>
  </Space.Compact>
}
