'use client'

import { useEffect, useState } from 'react'
import { PrismApp } from '@/components/prism/prism-app'
import { Onboarding } from '@/components/onboarding/onboarding'

export default function Page() {
  // Check if onboarding was completed (only on client, not server)
  // This prevents SSR hydration mismatch
  const [onboardingCompleted, setOnboardingCompleted] = useState<boolean | null>(null)

  useEffect(() => {
    const completed = localStorage.getItem('anna_onboarding_complete') === 'true'
    setOnboardingCompleted(completed)
  }, [])

  if (onboardingCompleted === null) {
    return <LoadingScreen />
  }

  return onboardingCompleted ? <PrismApp /> : <Onboarding />
}

function LoadingScreen() {
  return <div className="min-h-screen bg-background flex items-center justify-center">
    <div className="text-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      <p className="mt-4 text-muted-foreground">Loading...</p>
    </div>
  </div>
}

