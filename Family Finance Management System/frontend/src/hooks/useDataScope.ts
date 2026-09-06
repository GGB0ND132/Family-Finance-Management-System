import { useSearchParams } from 'react-router-dom'
import type { DataScope } from '../data/financeData'

export function useDataScope(): [DataScope, (scope: DataScope) => void] {
  const [params, setParams] = useSearchParams()
  const scope: DataScope = params.get('scope') === 'family' ? 'family' : 'personal'
  const setScope = (next: DataScope) => { const nextParams = new URLSearchParams(params); nextParams.set('scope', next); setParams(nextParams) }
  return [scope, setScope]
}
