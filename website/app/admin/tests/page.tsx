'use client'

import { useEffect, useState } from 'react'
import {
  CheckCircle2,
  XCircle,
  Clock,
  Activity,
  GitBranch,
  Calendar,
  PlayCircle,
} from 'lucide-react'

interface TestRun {
  id: number
  run_id: string
  run_type: 'ci' | 'deploy' | 'daily' | 'manual'
  started_at: string
  completed_at: string | null
  status: 'passed' | 'failed' | 'running'
  tests_total: number
  tests_passed: number
  tests_failed: number
  coverage_percent: number | null
  error_log: string | null
  created_at: string
}

interface TestData {
  runs: TestRun[]
  summary: {
    totalRuns: number
    passedRuns: number
    failedRuns: number
    passRate: string
    avgCoverage: string | null
  }
  byType: {
    ci: number
    deploy: number
    daily: number
    manual: number
  }
}

export default function TestsPage() {
  const [data, setData] = useState<TestData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchTests() {
      try {
        const res = await fetch('/api/tests')
        if (!res.ok) throw new Error('Failed to fetch test data')
        const result = await res.json()
        setData(result)
        setError(null)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load test data')
      } finally {
        setLoading(false)
      }
    }
    fetchTests()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-cream/70">Loading test history...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
        <p className="text-red-400">{error}</p>
      </div>
    )
  }

  if (!data) return null

  const { runs, summary, byType } = data

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-serif text-accent-beige">Test Dashboard</h1>
        <span className="text-cream/50 text-sm">Last 30 days</span>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <SummaryCard
          icon={<Activity className="w-5 h-5" />}
          label="Total Runs"
          value={summary.totalRuns.toString()}
        />
        <SummaryCard
          icon={<CheckCircle2 className="w-5 h-5 text-green-400" />}
          label="Pass Rate"
          value={`${summary.passRate}%`}
          highlight={parseFloat(summary.passRate) >= 90}
        />
        <SummaryCard
          icon={<XCircle className="w-5 h-5 text-red-400" />}
          label="Failed Runs"
          value={summary.failedRuns.toString()}
          alert={summary.failedRuns > 0}
        />
        <SummaryCard
          icon={<Clock className="w-5 h-5" />}
          label="Avg Coverage"
          value={summary.avgCoverage ? `${summary.avgCoverage}%` : 'N/A'}
        />
      </div>

      {/* Run Type Breakdown */}
      <div className="bg-navy-charcoal/50 rounded-2xl p-6">
        <h2 className="text-lg font-serif text-accent-beige mb-4">Runs by Type</h2>
        <div className="grid grid-cols-4 gap-4">
          <TypeCard icon={<GitBranch size={20} />} label="CI" count={byType.ci} />
          <TypeCard icon={<PlayCircle size={20} />} label="Deploy" count={byType.deploy} />
          <TypeCard icon={<Calendar size={20} />} label="Daily" count={byType.daily} />
          <TypeCard icon={<Activity size={20} />} label="Manual" count={byType.manual} />
        </div>
      </div>

      {/* Test Run History */}
      <div className="bg-navy-charcoal/50 rounded-2xl p-6">
        <h2 className="text-lg font-serif text-accent-beige mb-4">Recent Test Runs</h2>
        {runs.length === 0 ? (
          <p className="text-cream/50 text-center py-8">
            No test runs recorded yet. Tests will appear here after CI pipeline runs.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-accent-beige/20">
                  <th className="text-left py-3 text-cream/70 font-normal">Status</th>
                  <th className="text-left py-3 text-cream/70 font-normal">Type</th>
                  <th className="text-left py-3 text-cream/70 font-normal">Date</th>
                  <th className="text-right py-3 text-cream/70 font-normal">Passed</th>
                  <th className="text-right py-3 text-cream/70 font-normal">Failed</th>
                  <th className="text-right py-3 text-cream/70 font-normal">Coverage</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id} className="border-b border-accent-beige/10">
                    <td className="py-3">
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="py-3 text-cream capitalize">{run.run_type}</td>
                    <td className="py-3 text-cream/70">
                      {new Date(run.created_at).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="py-3 text-right text-green-400">{run.tests_passed}</td>
                    <td className="py-3 text-right text-red-400">{run.tests_failed}</td>
                    <td className="py-3 text-right text-accent-beige">
                      {run.coverage_percent ? `${run.coverage_percent}%` : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Test Categories Info */}
      <div className="bg-navy-charcoal/50 rounded-2xl p-6">
        <h2 className="text-lg font-serif text-accent-beige mb-4">Test Categories</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <CategoryCard
            name="Auth"
            description="OAuth flow and session management"
            schedule="CI"
          />
          <CategoryCard name="API" description="REST endpoint validation" schedule="CI" />
          <CategoryCard name="Website" description="Page rendering and components" schedule="CI" />
          <CategoryCard
            name="Data"
            description="Database integrity and freshness"
            schedule="Daily"
          />
          <CategoryCard
            name="TikTok"
            description="Publishing and API mocking"
            schedule="Daily"
          />
        </div>
      </div>
    </div>
  )
}

function SummaryCard({
  icon,
  label,
  value,
  highlight,
  alert,
}: {
  icon: React.ReactNode
  label: string
  value: string
  highlight?: boolean
  alert?: boolean
}) {
  return (
    <div
      className={`bg-navy-charcoal/50 rounded-xl p-4 ${highlight ? 'ring-1 ring-green-500/30' : ''} ${alert ? 'ring-1 ring-red-500/30' : ''}`}
    >
      <div className="flex items-center gap-2 text-accent-beige/70 mb-2">
        {icon}
        <span className="text-sm">{label}</span>
      </div>
      <div className="text-2xl font-serif text-accent-beige">{value}</div>
    </div>
  )
}

function TypeCard({
  icon,
  label,
  count,
}: {
  icon: React.ReactNode
  label: string
  count: number
}) {
  return (
    <div className="flex items-center gap-3 text-cream/70">
      <div className="text-accent-beige/70">{icon}</div>
      <div>
        <div className="text-sm text-cream/50">{label}</div>
        <div className="text-lg font-serif text-accent-beige">{count}</div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: 'passed' | 'failed' | 'running' }) {
  const styles = {
    passed: 'bg-green-500/20 text-green-400',
    failed: 'bg-red-500/20 text-red-400',
    running: 'bg-yellow-500/20 text-yellow-400',
  }

  const icons = {
    passed: <CheckCircle2 size={14} />,
    failed: <XCircle size={14} />,
    running: <Clock size={14} />,
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs ${styles[status]}`}
    >
      {icons[status]}
      {status}
    </span>
  )
}

function CategoryCard({
  name,
  description,
  schedule,
}: {
  name: string
  description: string
  schedule: string
}) {
  return (
    <div className="bg-navy/50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="font-medium text-cream">{name}</span>
        <span className="text-xs bg-accent-beige/20 text-accent-beige px-2 py-0.5 rounded">
          {schedule}
        </span>
      </div>
      <p className="text-sm text-cream/50">{description}</p>
    </div>
  )
}
