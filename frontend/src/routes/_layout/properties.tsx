import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/_layout/properties')({
  component: () =>( 
  <div>
    <div>Hello /_layout/properties!</div>
    <div>A little more</div>
  </div>
  
  )
})