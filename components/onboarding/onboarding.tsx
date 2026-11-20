"use client"

import { useEffect, useState } from "react"
import { Button } from "./ui/button"
import { useRouter } from "next/navigation"

export default function Onboarding() {
  const [step, setStep] = useState(1)
  const router = useRouter()
  const onboardingCompleted = localStorage.getItem("anna_onboarding_complete") === "true"

  // If somehow onboarding is marked complete, go straight to app
  if (onboardingCompleted) {
    router.replace("/")
    return null
  }

  const steps = [
    {
      title: "Welcome to Anna AI",
      content:
        "Transform your code with AI-powered analysis. Submit code and receive accessibility, quality, and efficiency feedback.",
    },
    {
      title: "Select Your Language",
      content:
        "Choose from 12 programming languages including Python, JavaScript/TypeScript, Go, Rust, Java, C#, and more.",
    },
    {
      title: "Submit Your First Code",
      content:
        "Paste your code below and click 'Review' to get started. Get instant feedback on your code's quality and accessibility.",
    },
    {
      title: "Explore Results",
      content:
        "Review your accessibility score, quality metrics, and efficiency insights. Fix issues and re-submit to improve your score.",
    },
  ]

  useEffect(() => {
    // Mark onboarding as complete after last step
    const completeOnboarding = () => {
      localStorage.setItem("anna_onboarding_complete", "true")
      router.replace("/")
    }

    if (step >= steps.length) {
      completeOnboarding()
    }
  }, [step, router])

  const handleNext = () => {
    setStep((prev) => prev + 1)
  }

  const currentStep = steps[step - 1] || steps[steps.length - 1]

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-desc mb-4">{currentStep.title}</h2>
        <p className="text-text mb-6">{currentStep.content}</p>

        <div className="space-y-4">
          {currentStep.title !== "Submit Your First Code" ? (
            <Button
              onClick={handleNext}
              className="w-full"
            >
              {step < steps.length ? "Next" : "Get Started"}
            </Button>
          ) : (
            <div className="space-y-2">
              <Button
                onClick={handleNext}
                className="w-full bg-primary/20 text-primary"
              >
                Review My Code
              </Button>
              <p className="text-xs text-muted-foreground">
                Paste code below and click above to get started
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}