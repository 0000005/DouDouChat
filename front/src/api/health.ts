import { getApiBaseUrl } from './base'

export interface HealthStatus {
    status: string
    llm_configured: boolean
    embedding_configured: boolean
}

export async function checkHealth(): Promise<HealthStatus> {
    const response = await fetch(`${getApiBaseUrl()}/api/health`)
    if (!response.ok) {
        throw new Error('Health check failed')
    }
    return response.json()
}
