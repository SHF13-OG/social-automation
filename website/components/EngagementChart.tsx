'use client'

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
} from 'recharts'

interface Post {
  post_id: string
  created_at: string
  views: number
  likes: number
  comments: number
  shares: number
  favorites: number
}

interface EngagementChartProps {
  posts: Post[]
  type: 'views' | 'engagement'
}

export default function EngagementChart({ posts, type }: EngagementChartProps) {
  // Sort posts by date and prepare chart data
  const chartData = [...posts]
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .map((post) => {
      const date = new Date(post.created_at).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
      })
      const engagement = (post.likes || 0) + (post.comments || 0) + (post.shares || 0)
      const engagementRate = post.views > 0 ? ((engagement / post.views) * 100).toFixed(2) : 0

      return {
        date,
        views: post.views || 0,
        engagement,
        engagementRate: Number(engagementRate),
        likes: post.likes || 0,
        comments: post.comments || 0,
        shares: post.shares || 0,
      }
    })

  if (type === 'views') {
    return (
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#3d4a5c" />
            <XAxis
              dataKey="date"
              stroke="#f5f0e8"
              fontSize={12}
              tickLine={false}
            />
            <YAxis
              stroke="#f5f0e8"
              fontSize={12}
              tickLine={false}
              tickFormatter={(value) => value >= 1000 ? `${(value / 1000).toFixed(1)}k` : value}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#252f3f',
                border: '1px solid #E8D5B7',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#E8D5B7' }}
              itemStyle={{ color: '#f5f0e8' }}
            />
            <Bar dataKey="views" fill="#E8D5B7" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#3d4a5c" />
          <XAxis
            dataKey="date"
            stroke="#f5f0e8"
            fontSize={12}
            tickLine={false}
          />
          <YAxis
            stroke="#f5f0e8"
            fontSize={12}
            tickLine={false}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#252f3f',
              border: '1px solid #E8D5B7',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#E8D5B7' }}
            itemStyle={{ color: '#f5f0e8' }}
            formatter={(value: number) => [`${value.toFixed(2)}%`, 'Engagement Rate']}
          />
          <Line
            type="monotone"
            dataKey="engagementRate"
            stroke="#E8D5B7"
            strokeWidth={2}
            dot={{ fill: '#E8D5B7', strokeWidth: 2 }}
            activeDot={{ r: 6, fill: '#E8D5B7' }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
