import React from 'react';
import Card, { CardData } from './course-design-cards';

export const CourseDesignCardsDemo: React.FC = () => {
  const cardData: CardData[] = [
    {
      id: 1,
      colorClass: 'green',
      date: 'Feb 2, 2026',
      title: 'Technical Skilling & Placement',
      description: 'Tata STRIVE Pune batch career transitions & TCS recruitment drive',
      progressPercent: '90%',
      progressValue: '90% Positive',
      imgSrc1: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&h=100&fit=crop&crop=face',
      imgAlt1: 'Alumnus Rohan',
      imgSrc2: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face',
      imgAlt2: 'Mentor Meera',
      countdownText: '4 comments',
    },
    {
      id: 2,
      colorClass: 'orange',
      date: 'Feb 05, 2026',
      title: 'Solar Technician Module',
      description: 'Women technicians training in solar diagnostics at Kalinganagar Odisha',
      progressPercent: '75%',
      progressValue: '75% Positive',
      imgSrc1: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=100&h=100&fit=crop&crop=face',
      imgAlt1: 'Trainee Sunita',
      imgSrc2: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop&crop=face',
      imgAlt2: 'Instructor Pravin',
      countdownText: '3 comments',
    },
    {
      id: 3,
      colorClass: 'red',
      date: 'March 03, 2026',
      title: 'Portal Certificate Dispatch',
      description: 'NSDC Skill India verification credential sync for Mohali cohort',
      progressPercent: '42%',
      progressValue: '42% Neutral/Attention',
      imgSrc1: 'https://images.unsplash.com/photo-1522075469751-3a6694fb2f61?w=100&h=100&fit=crop&crop=face',
      imgAlt1: 'Student Amit',
      imgSrc2: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop&crop=face',
      imgAlt2: 'Support Neha',
      countdownText: '3 tickets',
    },
    {
      id: 4,
      colorClass: 'blue',
      date: 'March 08, 2026',
      title: 'Titan Retail & Optometry Lab',
      description: 'Hands-on practical eye testing & store management customer curriculum',
      progressPercent: '88%',
      progressValue: '88% Positive',
      imgSrc1: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=100&fit=crop&crop=face',
      imgAlt1: 'Trainee Karthik',
      imgSrc2: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?w=100&h=100&fit=crop&crop=face',
      imgAlt2: 'Partner Lead Latha',
      countdownText: '3 comments',
    },
  ];

  return (
    <section className="course-cards-container">
      {cardData.map((card) => (
        <Card key={card.id} data={card} />
      ))}
    </section>
  );
};

export default CourseDesignCardsDemo;
