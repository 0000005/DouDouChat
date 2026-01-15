import { ref } from 'vue'
import packageJson from '../../package.json'

const GITHUB_PACKAGE_JSON_URL = 'https://raw.githubusercontent.com/0000005/WeChatAgent/refs/heads/master/package.json'
const GITHUB_RELEASES_URL = 'https://github.com/0000005/WeChatAgent/releases'

export function useUpdateCheck() {
    const isChecking = ref(false)
    const latestVersion = ref('')
    const currentVersion = packageJson.version
    const updateAvailable = ref(false)
    const error = ref<string | null>(null)

    const compareVersions = (v1: string, v2: string) => {
        const parts1 = v1.split('.').map(Number)
        const parts2 = v2.split('.').map(Number)

        // Ensure we handle cases like 0.1.0 vs 0.1
        const length = Math.max(parts1.length, parts2.length)
        for (let i = 0; i < length; i++) {
            const p1 = parts1[i] || 0
            const p2 = parts2[i] || 0
            if (p1 > p2) return 1
            if (p1 < p2) return -1
        }
        return 0
    }

    const checkUpdate = async () => {
        isChecking.value = true
        error.value = null
        try {
            // Add timestamp to avoid caching
            const response = await fetch(`${GITHUB_PACKAGE_JSON_URL}?timestamp=${Date.now()}`)
            if (!response.ok) throw new Error('无法获取版本信息')
            const data = await response.json()
            latestVersion.value = data.version

            if (compareVersions(latestVersion.value, currentVersion) > 0) {
                updateAvailable.value = true
                return true
            } else {
                updateAvailable.value = false
                return false
            }
        } catch (e: any) {
            console.error('Update check failed:', e)
            error.value = e.message
            return false
        } finally {
            isChecking.value = false
        }
    }

    const openReleases = () => {
        if ((window as any).WeAgentChat?.shell) {
            (window as any).WeAgentChat.shell.openExternal(GITHUB_RELEASES_URL)
        } else {
            window.open(GITHUB_RELEASES_URL, '_blank')
        }
    }

    return {
        isChecking,
        latestVersion,
        currentVersion,
        updateAvailable,
        error,
        checkUpdate,
        openReleases
    }
}
