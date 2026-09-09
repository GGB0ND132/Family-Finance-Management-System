import { Navigate, useSearchParams } from 'react-router-dom'
import { PersonalPage } from './PersonalPage'
import { FamilyDashboardPage } from './FamilyDashboardPage'

/** 统一首页容器：通过 URL 的 scope 参数在个人与家庭视图间切换。 */
export function HomePage() {
  const [params] = useSearchParams()
  return params.get('scope') === 'family' ? <FamilyDashboardPage /> : <PersonalPage />
}

export function LegacyHomeRedirect({ scope }: { scope: 'personal' | 'family' }) {
  return <Navigate to={`/home?scope=${scope}`} replace />
}
