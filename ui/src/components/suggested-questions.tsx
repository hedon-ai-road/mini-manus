'use client'

import { cn } from "@/lib/utils";
import { Button } from "./ui/button";

interface SuggestedQuestionsProps {
    className?: string;
}

export function SuggestedQuestions({className}: SuggestedQuestionsProps) {
    return (
        <div className={cn('flex flex-wrap gap-2 sm:gap-3', className)}>
            <Button variant="outline" className="cursor-pointer">这个建筑有多少层？</Button>
            <Button variant="outline" className="cursor-pointer">与世界最高建筑相比有多高？</Button>
            <Button variant="outline" className="cursor-pointer">建造该建筑用了多长时间？</Button>
            <Button variant="outline" className="cursor-pointer">这个建筑的用途是什么？</Button>
        </div>
    )
}