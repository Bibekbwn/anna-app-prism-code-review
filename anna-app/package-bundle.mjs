import { cp, mkdir, rm } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const projectRoot = fileURLToPath(new URL('../', import.meta.url))
const exportDirectory = path.join(projectRoot, 'out')
const bundleDirectory = path.join(projectRoot, 'anna-app', 'bundle')

await rm(bundleDirectory, { recursive: true, force: true })
await mkdir(bundleDirectory, { recursive: true })
await cp(exportDirectory, bundleDirectory, { recursive: true })

console.log(`Anna static bundle prepared at ${bundleDirectory}`)
