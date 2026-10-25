import { useLightcone } from '../context/LightconeContext'
import StateGate from '../app/StateGate'
import PolicyPicker from '../components/PolicyPicker'

export default function PolicyPage() {
  const { date, setDate, setState } = useLightcone()
  return (
    <StateGate>
      {(s) => <PolicyPicker state={s} date={date} onDateChange={setDate} onChanged={setState} />}
    </StateGate>
  )
}
