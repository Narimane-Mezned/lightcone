import { useLightcone } from '../context/LightconeContext'
import StateGate from '../app/StateGate'
import DemoRunner from '../components/DemoRunner'
import NodePanel from '../components/NodePanel'
import Spacetime from '../components/Spacetime'

export default function SimulationPage() {
  const { state, setState, refresh } = useLightcone()
  return (
    <div className="flex flex-col gap-4">
      <DemoRunner state={state} onChanged={setState} />
      <StateGate>
        {(s) => (
          <div className="grid grid-cols-[280px_1fr_280px] gap-4">
            <NodePanel node="earth" state={s} onBooked={refresh} />
            <Spacetime state={s} />
            <NodePanel node="mars" state={s} onBooked={refresh} />
          </div>
        )}
      </StateGate>
    </div>
  )
}
