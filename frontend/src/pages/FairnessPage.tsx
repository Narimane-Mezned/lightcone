import { useLightcone } from '../context/LightconeContext'
import FairnessLab from '../components/FairnessLab'

export default function FairnessPage() {
  const { date } = useLightcone()
  return <FairnessLab date={date} />
}
