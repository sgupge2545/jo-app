"use client";

import { useState } from "react";
import { ArrowLeft, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Label } from "@/components/ui/label";

// サンプルデータ
type Subject = {
  id: number;
  title: string;
  name: string;
  lecturer: string;
  time: string;
  category: string;
  code: string;
};

type TimetableData = {
  [day: string]: {
    [period: string]: Subject | null;
  };
};

const sampleTimetable: TimetableData = {
  "1": {
    "1": {
      id: 123,
      title: "人工知能実験",
      name: "AI実験",
      lecturer: "山口 暢彦",
      time: "月１",
      category: "専門科目",
      code: "CS301",
    },
    "2": null,
    "3": {
      id: 124,
      title: "データベース設計",
      name: "DB設計",
      lecturer: "田中 美咲",
      time: "月３",
      category: "専門科目",
      code: "CS302",
    },
    "4": {
      id: 125,
      title: "人工知能実験",
      name: "AI実験",
      lecturer: "山口 暢彦",
      time: "月４",
      category: "専門科目",
      code: "CS301",
    },
    "5": {
      id: 126,
      title: "人工知能実験",
      name: "AI実験",
      lecturer: "山口 暢彦",
      time: "月５",
      category: "専門科目",
      code: "CS301",
    },
    "6": null,
  },
  "2": {
    "1": null,
    "2": {
      id: 127,
      title: "英語コミュニケーション",
      name: "英語",
      lecturer: "Smith John",
      time: "火２",
      category: "一般科目",
      code: "EN201",
    },
    "3": {
      id: 128,
      title: "統計学基礎",
      name: "統計学",
      lecturer: "佐藤 健一",
      time: "火３",
      category: "基礎科目",
      code: "MA301",
    },
    "4": null,
    "5": null,
    "6": null,
  },
  "3": {
    "1": {
      id: 129,
      title: "ソフトウェア工学",
      name: "SW工学",
      lecturer: "鈴木 太郎",
      time: "水１",
      category: "専門科目",
      code: "CS401",
    },
    "2": null,
    "3": null,
    "4": {
      id: 130,
      title: "プログラミング演習",
      name: "プログラミング",
      lecturer: "高橋 花子",
      time: "水４",
      category: "専門科目",
      code: "CS201",
    },
    "5": {
      id: 131,
      title: "プログラミング演習",
      name: "プログラミング",
      lecturer: "高橋 花子",
      time: "水５",
      category: "専門科目",
      code: "CS201",
    },
    "6": null,
  },
  "4": {
    "1": null,
    "2": null,
    "3": {
      id: 132,
      title: "経済学入門",
      name: "経済学",
      lecturer: "伊藤 次郎",
      time: "木３",
      category: "一般科目",
      code: "EC101",
    },
    "4": null,
    "5": null,
    "6": null,
  },
  "5": {
    "1": null,
    "2": {
      id: 133,
      title: "体育実技",
      name: "体育",
      lecturer: "渡辺 強",
      time: "金２",
      category: "一般科目",
      code: "PE101",
    },
    "3": null,
    "4": null,
    "5": null,
    "6": null,
  },
};

const users = [
  { id: "1", name: "田中 太郎" },
  { id: "2", name: "佐藤 花子" },
  { id: "3", name: "山田 次郎" },
];

const dayNames = ["月", "火", "水", "木", "金"];
const periods = ["1限", "2限", "3限", "4限", "5限", "6限"];
const timeSlots = [
  "9:00-10:30",
  "10:40-12:10",
  "13:00-14:30",
  "14:40-16:10",
  "16:20-17:50",
  "18:00-19:30",
];

const availableSubjects = [
  {
    id: "201",
    name: "データ構造とアルゴリズム",
    lecturer: "田中 一郎",
    category: "専門科目",
  },
  {
    id: "202",
    name: "オペレーティングシステム",
    lecturer: "佐藤 二郎",
    category: "専門科目",
  },
  {
    id: "203",
    name: "ネットワーク基礎",
    lecturer: "鈴木 三郎",
    category: "専門科目",
  },
  { id: "204", name: "線形代数", lecturer: "高橋 四郎", category: "基礎科目" },
  { id: "205", name: "微分積分", lecturer: "伊藤 五郎", category: "基礎科目" },
  {
    id: "206",
    name: "英語会話",
    lecturer: "Johnson Mary",
    category: "一般科目",
  },
  { id: "207", name: "哲学入門", lecturer: "山田 六郎", category: "一般科目" },
  {
    id: "208",
    name: "心理学基礎",
    lecturer: "渡辺 七子",
    category: "一般科目",
  },
];

const getPeriodColor = (period: number) => {
  switch (period) {
    case 1:
      return "bg-blue-50 border-blue-200 text-blue-800";
    case 2:
      return "bg-green-50 border-green-200 text-green-800";
    case 3:
      return "bg-orange-50 border-orange-200 text-orange-800";
    case 4:
      return "bg-purple-50 border-purple-200 text-purple-800";
    case 5:
      return "bg-pink-50 border-pink-200 text-pink-800";
    case 6:
      return "bg-indigo-50 border-indigo-200 text-indigo-800";
    default:
      return "bg-gray-50 border-gray-200 text-gray-800";
  }
};

export default function TimetablePage() {
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedDay, setSelectedDay] = useState<number>(0);
  const [selectedPeriod, setSelectedPeriod] = useState<number>(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{
    day: number;
    period: number;
    subject: Subject;
  } | null>(null);

  const handleBack = () => {
    // 戻る処理（実際のアプリでは router.back() など）
    console.log("戻るボタンがクリックされました");
  };

  const handleAddSubject = (day: number, period: number) => {
    setSelectedDay(day);
    setSelectedPeriod(period);
    setIsDialogOpen(true);
    setSearchQuery("");
    setSelectedSubjectId("");
  };

  const handleCancel = () => {
    setIsDialogOpen(false);
    setSearchQuery("");
    setSelectedSubjectId("");
  };

  const handleAdd = () => {
    // 実際の追加処理はここに実装
    console.log(
      `科目ID: ${selectedSubjectId} を ${selectedDay}曜日${selectedPeriod}限に追加`
    );
    setIsDialogOpen(false);
    setSearchQuery("");
    setSelectedSubjectId("");
  };

  const handleDeleteSubject = (
    day: number,
    period: number,
    subject: Subject
  ) => {
    setDeleteTarget({ day, period, subject });
    setIsDeleteDialogOpen(true);
  };

  const handleCancelDelete = () => {
    setIsDeleteDialogOpen(false);
    setDeleteTarget(null);
  };

  const handleConfirmDelete = () => {
    if (deleteTarget) {
      console.log(
        `${deleteTarget.subject.name} を ${dayNames[deleteTarget.day - 1]}曜日${
          deleteTarget.period
        }限から削除`
      );
    }
    setIsDeleteDialogOpen(false);
    setDeleteTarget(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* ヘッダー */}
      <div className="flex items-center justify-between mb-6">
        <Button
          variant="outline"
          size="sm"
          onClick={handleBack}
          className="flex items-center gap-2 bg-transparent"
        >
          <ArrowLeft className="h-4 w-4" />
          戻る
        </Button>

        <Select value={selectedUser} onValueChange={setSelectedUser}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="ユーザーを選択" />
          </SelectTrigger>
          <SelectContent>
            {users.map((user) => (
              <SelectItem key={user.id} value={user.id}>
                {user.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* 時間割タイトル */}
      <div className="text-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">時間割</h1>
      </div>

      {/* 時間割テーブル */}
      <div className="max-w-5xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
          {/* ヘッダー行 */}
          <div className="grid grid-cols-6 bg-gray-100 border-b">
            <div className="p-2 text-center font-medium text-gray-700 border-r text-sm">
              時限
            </div>
            {dayNames.map((day, index) => (
              <div
                key={index}
                className="p-2 text-center font-medium text-gray-700 border-r last:border-r-0 text-sm"
              >
                {day}曜日
              </div>
            ))}
          </div>

          {/* 時間割の行 */}
          {periods.map((period, periodIndex) => (
            <div
              key={periodIndex}
              className="grid grid-cols-6 border-b last:border-b-0"
            >
              {/* 時限列 */}
              <div className="p-2 bg-gray-50 border-r flex flex-col items-center justify-center">
                <div className="font-medium text-gray-700 text-sm">
                  {period}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {timeSlots[periodIndex]}
                </div>
              </div>

              {/* 各曜日の授業 */}
              {dayNames.map((_, dayIndex) => {
                const dayKey = (dayIndex + 1).toString();
                const periodKey = (periodIndex + 1).toString();
                const subject = sampleTimetable[dayKey]?.[periodKey];

                return (
                  <div
                    key={dayIndex}
                    className="p-1.5 border-r last:border-r-0 h-[100px]"
                  >
                    {subject ? (
                      <Card
                        className={`h-full p-1 ${getPeriodColor(
                          periodIndex + 1
                        )} group relative`}
                      >
                        <CardContent className="p-1 h-full flex gap-1 flex-col justify-between">
                          <div>
                            <div className="font-medium leading-tight pr-6">
                              {subject.name}
                            </div>
                            <div className="text-xs text-gray-600">
                              {subject.lecturer}
                            </div>
                          </div>
                          <div className="text-xs px-1 py-0.5 bg-white/50 rounded text-center">
                            {subject.category}
                          </div>

                          {/* 削除ボタン */}
                          <Button
                            variant="ghost"
                            size="sm"
                            className="absolute top-1 right-1 w-5 h-5 p-0 opacity-0 group-hover:opacity-100 transition-opacity bg-red-50 hover:bg-red-100 text-red-600"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteSubject(
                                dayIndex + 1,
                                periodIndex + 1,
                                subject
                              );
                            }}
                          >
                            <X className="h-2.5 w-2.5" />
                          </Button>
                        </CardContent>
                      </Card>
                    ) : (
                      <div className="h-full flex items-center justify-center">
                        <Button
                          variant="outline"
                          size="sm"
                          className="w-7 h-7 p-0 text-gray-400 hover:text-gray-600 border-dashed bg-transparent"
                          onClick={() =>
                            handleAddSubject(dayIndex + 1, periodIndex + 1)
                          }
                        >
                          <Plus className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* 科目追加ダイアログ */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>科目を追加</DialogTitle>
            <p className="text-sm text-gray-600">
              {dayNames[selectedDay - 1]}曜日 {selectedPeriod}
              限に追加する科目を選択してください
            </p>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="subject-search">科目を検索</Label>
              <Command className="border rounded-md">
                <CommandInput
                  placeholder="科目名で検索..."
                  value={searchQuery}
                  onValueChange={setSearchQuery}
                />
                <CommandList className="max-h-48">
                  <CommandEmpty>該当する科目が見つかりません</CommandEmpty>
                  <CommandGroup>
                    {availableSubjects
                      .filter(
                        (subject) =>
                          subject.name
                            .toLowerCase()
                            .includes(searchQuery.toLowerCase()) ||
                          subject.lecturer
                            .toLowerCase()
                            .includes(searchQuery.toLowerCase())
                      )
                      .map((subject) => (
                        <CommandItem
                          key={subject.id}
                          value={subject.id}
                          onSelect={() => setSelectedSubjectId(subject.id)}
                          className={
                            selectedSubjectId === subject.id ? "bg-blue-50" : ""
                          }
                        >
                          <div className="flex flex-col w-full">
                            <div className="font-medium">{subject.name}</div>
                            <div className="text-sm text-gray-600">
                              {subject.lecturer}
                            </div>
                            <div className="text-xs text-gray-500">
                              {subject.category}
                            </div>
                          </div>
                        </CommandItem>
                      ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </div>
          </div>

          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={handleCancel}>
              キャンセル
            </Button>
            <Button onClick={handleAdd} disabled={!selectedSubjectId}>
              追加
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 科目削除確認ダイアログ */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>科目を削除</DialogTitle>
          </DialogHeader>

          <div className="py-4">
            {deleteTarget && (
              <p className="text-sm text-gray-600">
                <span className="font-medium">{deleteTarget.subject.name}</span>
                （{deleteTarget.subject.lecturer}）を
                <span className="font-medium">
                  {dayNames[deleteTarget.day - 1]}曜日{deleteTarget.period}限
                </span>
                から削除しますか？
              </p>
            )}
          </div>

          <DialogFooter className="flex gap-2">
            <Button variant="outline" onClick={handleCancelDelete}>
              キャンセル
            </Button>
            <Button variant="destructive" onClick={handleConfirmDelete}>
              削除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
