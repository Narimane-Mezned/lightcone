import StateGate from '../app/StateGate'
import Receipts from '../components/Receipts'

export default function ReceiptsPage() {
  return <StateGate>{(s) => <Receipts state={s} />}</StateGate>
}
