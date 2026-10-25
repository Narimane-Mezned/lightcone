import StateGate from '../app/StateGate'
import NaiveComparison from '../components/NaiveComparison'

export default function ComparisonPage() {
  return <StateGate>{(s) => <NaiveComparison state={s} />}</StateGate>
}
