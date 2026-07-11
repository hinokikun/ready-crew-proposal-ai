"use client";

import { memo } from "react";
import { Bot, Clock3 } from "lucide-react";
import type { ActivityItem } from "./types";

type ActivityFeedProps = {
  activities: ActivityItem[];
};

export const ActivityFeed = memo(function ActivityFeed({ activities }: ActivityFeedProps) {
  return (
    <section className="operations-activity-feed" id="notifications-panel" aria-label="AI活動ログ">
      <div className="operations-section-heading">
        <div>
          <p className="eyebrow">AI Activity Feed</p>
          <h2>AI活動ログ</h2>
        </div>
        <span>最新20件</span>
      </div>

      <div className="operations-feed-list">
        {activities.length ? (
          activities.map((item) => (
            <article className="operations-feed-item" key={item.id}>
              <div className="operations-feed-agent">
                <Bot size={16} aria-hidden="true" />
                <span>{item.agent}</span>
              </div>
              <div>
                <strong>{item.title}</strong>
                <p>{item.detail}</p>
              </div>
              <time>
                <Clock3 size={13} aria-hidden="true" />
                {item.time}
              </time>
            </article>
          ))
        ) : (
          <p className="helper-text">まだAI活動ログはありません。</p>
        )}
      </div>
    </section>
  );
});
