import { Segmented } from 'antd'
import type { DataScope } from '../data/financeData'
import { useDataScope } from '../hooks/useDataScope'

export function ScopeToggle({ value = 'personal', onChange }: { value?: DataScope; onChange?: (scope: DataScope) => void }) {
  const [urlScope, setUrlScope] = useDataScope()
  const current = onChange || value !== 'personal' ? value : urlScope
  const change = (next: string | number) => {
    const scope = next as DataScope
    if (onChange) onChange(scope)
    else setUrlScope(scope)
  }
  return <Segmented aria-label="数据范围" value={current} onChange={change} options={[{ value: 'personal', label: '个人' }, { value: 'family', label: '家庭' }]} />
}
