'use client'

import { PrismApp } from '@/components/prism/prism-app'
import { Onboarding } from '@/components/onboarding/onboarding'

export default function Page() {
  // Check if onboarding was completed
  const onboardingCompleted = typeof window !== 'undefined' &&
    window.localStorage.getItem('anna_onboarding_complete') === 'true'
  
  return onboardingCompleted ? <PrismApp /> : <Onboarding />
}

