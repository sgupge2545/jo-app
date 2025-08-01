"use client";

import { useState, useEffect } from "react";

// CSSスピナーのスタイル
const spinnerStyles = `
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
  
  .loading-spinner {
    border: 3px solid #f3f4f6;
    border-top: 3px solid #3b82f6;
    border-radius: 50%;
    width: 48px;
    height: 48px;
    animation: spin 1s linear infinite;
  }
  
  .loading-spinner-small {
    border: 2px solid #f3f4f6;
    border-top: 2px solid #3b82f6;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    animation: spin 1s linear infinite;
  }
`;
import { ArrowLeft, Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
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

type User = {
  id: string;
  name: string;
};

type Subject = {
  id: number;
  title: string;
  name: string;
  lecturer: string;
  time: string;
  category: string;
  code: string;
  grade: string;
  class_name: string;
  season: string;
};

type TimetableData = {
  [day: string]: {
    [period: string]: Subject | null;
  };
};

const dayNames = ["月", "火", "水", "木", "金"];
const periods = [1, 2, 3, 4, 5, 6];
const timeSlots = ["1限", "2限", "3限", "4限", "5限", "6限"];

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

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";

// 検索条件判定用の関数
function subjectMatchesQuery(subject: Subject, query: string): boolean {
  const trimmedQuery = query.trim().toLowerCase();
  const nameMatch = subject.name.toLowerCase().includes(trimmedQuery);
  const lecturerMatch = subject.lecturer.toLowerCase().includes(trimmedQuery);

  return nameMatch || lecturerMatch;
}

export default function TimetablePage() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<string>("");
  const [myUserId, setMyUserId] = useState<string>("");
  const [timetable, setTimetable] = useState<TimetableData | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [selectedPeriod, setSelectedPeriod] = useState<number | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedSubjectId, setSelectedSubjectId] = useState("");
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<{
    day: number;
    period: number;
    subject: Subject;
  } | null>(null);
  const [availableSubjects, setAvailableSubjects] = useState<Subject[]>([]);
  const [availableSubjectsLoading, setAvailableSubjectsLoading] =
    useState(false);

  // シラバスモーダル用の状態
  const [syllabusModalOpen, setSyllabusModalOpen] = useState(false);
  const [syllabusModalHtml, setSyllabusModalHtml] = useState<string | null>(
    null
  );
  const [syllabusModalLoading, setSyllabusModalLoading] = useState(false);
  const [syllabusModalError, setSyllabusModalError] = useState<string | null>(
    null
  );

  // ローディング状態
  const [initialLoading, setInitialLoading] = useState(true);
  const [timetableLoading, setTimetableLoading] = useState(false);

  // ユーザー選択時に時間割を取得
  useEffect(() => {
    if (!selectedUser) {
      setTimetable(null);
      setTimetableLoading(false);
      return;
    }
    const fetchTimetable = async () => {
      setTimetableLoading(true);
      try {
        const res = await fetch(
          `${BACKEND_URL}/users/${selectedUser}/timetable`
        );
        if (!res.ok) throw new Error("時間割の取得に失敗しました");
        const data = await res.json();
        setTimetable(data.timetable);
      } catch {
        setTimetable(null);
      } finally {
        setTimetableLoading(false);
      }
    };
    fetchTimetable();
  }, [selectedUser]);

  useEffect(() => {
    // 初回マウント時にユーザーリストを取得してから認証中ユーザーを設定
    const initializeData = async () => {
      try {
        // まずユーザーリストを取得
        const usersRes = await fetch(`${BACKEND_URL}/users`);
        const usersData = await usersRes.json();
        setUsers(usersData);

        // 新APIで認証中ユーザー情報を取得
        const meRes = await fetch(`${BACKEND_URL}/me`, {
          credentials: "include",
        });
        if (meRes.ok) {
          const meData = await meRes.json();
          setSelectedUser(meData.id);
          setMyUserId(meData.id);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setInitialLoading(false);
      }
    };

    initializeData();
  }, []);

  useEffect(() => {
    if (!isDialogOpen || selectedDay == null || selectedPeriod == null) {
      setAvailableSubjects([]);
      setAvailableSubjectsLoading(false);
      return;
    }
    const fetchAvailableSubjects = async () => {
      setAvailableSubjectsLoading(true);
      try {
        const res = await fetch(
          `${BACKEND_URL}/available-lectures?day=${
            dayNames[selectedDay - 1]
          }&period=${selectedPeriod}`
        );
        if (!res.ok) throw new Error("科目一覧の取得に失敗しました");
        const data = await res.json();
        setAvailableSubjects(data);
      } catch (e) {
        console.error(e);
        setAvailableSubjects([]);
      } finally {
        setAvailableSubjectsLoading(false);
      }
    };
    fetchAvailableSubjects();
  }, [isDialogOpen, selectedDay, selectedPeriod]);

  const handleBack = () => {
    const FRONTEND_URL = process.env.NEXT_PUBLIC_FRONTEND_URL || "";
    window.location.href = `${FRONTEND_URL}/`;
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

  // 科目追加APIリクエスト
  const handleAdd = async () => {
    if (!selectedUser || !selectedSubjectId) return;
    try {
      const res = await fetch(
        `${BACKEND_URL}/timetables/${selectedUser}/lectures`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            day_of_week: selectedDay,
            period: selectedPeriod,
            lecture_id: Number(selectedSubjectId),
          }),
        }
      );
      if (!res.ok) throw new Error("追加に失敗しました");
      // 追加後、再取得
      const timetableRes = await fetch(
        `${BACKEND_URL}/users/${selectedUser}/timetable`
      );
      const data = await timetableRes.json();
      setTimetable(data.timetable);
      toast.success("追加しました");
    } catch (e) {
      console.error(e);
    }
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

  // 科目削除APIリクエスト
  const handleConfirmDelete = async () => {
    if (!deleteTarget || !selectedUser) return;
    try {
      const res = await fetch(
        `${BACKEND_URL}/timetables/${selectedUser}/lectures/remove`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            day_of_week: deleteTarget.day,
            period: deleteTarget.period,
          }),
        }
      );
      if (!res.ok) throw new Error("削除に失敗しました");
      // 削除後、再取得
      const timetableRes = await fetch(
        `${BACKEND_URL}/users/${selectedUser}/timetable`
      );
      const data = await timetableRes.json();
      setTimetable(data.timetable);
    } catch (e) {
      console.error(e);
    }
    setIsDeleteDialogOpen(false);
    setDeleteTarget(null);
  };

  // シラバスモーダルを開く
  const handleSyllabusClick = async (code: string) => {
    setSyllabusModalOpen(true);
    setSyllabusModalHtml(null);
    setSyllabusModalLoading(true);
    setSyllabusModalError(null);
    try {
      const res = await fetch(`${BACKEND_URL}/syllabuses/${code}`);
      if (!res.ok) throw new Error("シラバスの取得に失敗しました");
      const html = await res.text();
      setSyllabusModalHtml(html);
    } catch (e) {
      setSyllabusModalError(
        e instanceof Error ? e.message : "エラーが発生しました"
      );
    } finally {
      setSyllabusModalLoading(false);
    }
  };

  // 初期ローディング画面
  if (initialLoading) {
    return (
      <>
        <style>{spinnerStyles}</style>
        <div className="min-h-screen bg-gray-50 flex items-center justify-center">
          <div className="text-center">
            <div className="loading-spinner mx-auto mb-4"></div>
            <p className="text-gray-600 text-lg">データを読み込み中...</p>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <style>{spinnerStyles}</style>
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

          <div className="flex items-center gap-4">
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
            {timetableLoading ? (
              <div className="p-8 text-center">
                <div className="loading-spinner-small mx-auto mb-3"></div>
                <p className="text-gray-600">時間割を読み込み中...</p>
              </div>
            ) : (
              periods.map((period, periodIndex) => (
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
                    const subject = timetable?.[dayKey]?.[periodKey] || null;

                    return (
                      <div
                        key={dayIndex}
                        className="p-1.5 border-r last:border-r-0 h-[100px]"
                      >
                        {subject ? (
                          <Card
                            className={`h-full p-1 ${getPeriodColor(
                              periodIndex + 1
                            )} group relative cursor-pointer hover:shadow-md transition-shadow`}
                            onClick={() =>
                              subject.code && handleSyllabusClick(subject.code)
                            }
                            title="クリックでシラバス詳細を表示"
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
                              {selectedUser === myUserId && (
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
                              )}
                            </CardContent>
                          </Card>
                        ) : (
                          <div className="h-full flex items-center justify-center">
                            {selectedUser === myUserId && (
                              <Button
                                variant="outline"
                                size="sm"
                                className="w-7 h-7 p-0 text-gray-400 hover:text-gray-600 border-dashed bg-transparent"
                                onClick={() =>
                                  handleAddSubject(
                                    dayIndex + 1,
                                    periodIndex + 1
                                  )
                                }
                              >
                                <Plus className="h-3.5 w-3.5" />
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        </div>

        {/* 科目追加ダイアログ */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>科目を追加</DialogTitle>
              <p className="text-sm text-gray-600">
                {selectedDay != null ? `${dayNames[selectedDay - 1]}曜日` : ""}{" "}
                {selectedPeriod ?? ""}
                限に追加する科目を選択してください
              </p>
            </DialogHeader>

            <div className="space-y-4">
              <div>
                <Label htmlFor="subject-search">科目を検索</Label>
                <Command className="border rounded-md" shouldFilter={false}>
                  <CommandInput
                    placeholder="科目名で検索..."
                    value={searchQuery}
                    onValueChange={setSearchQuery}
                  />
                  {availableSubjectsLoading ? (
                    <div className="flex justify-center items-center py-6">
                      <div className="loading-spinner-small"></div>
                      <span className="ml-2 text-gray-500 text-sm">
                        科目情報を取得中...
                      </span>
                    </div>
                  ) : (
                    <CommandList className="max-h-48">
                      <CommandEmpty>該当する科目が見つかりません</CommandEmpty>
                      <CommandGroup>
                        {availableSubjects
                          .filter((subject) =>
                            subjectMatchesQuery(subject, searchQuery)
                          )
                          .map((subject) => (
                            <CommandItem
                              key={subject.id}
                              value={subject.name}
                              onSelect={() =>
                                setSelectedSubjectId(String(subject.id))
                              }
                              className={
                                selectedSubjectId === String(subject.id)
                                  ? "bg-blue-50"
                                  : ""
                              }
                            >
                              <div className="flex flex-col w-full">
                                <div className="font-medium">
                                  {subject.name}
                                </div>
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
                  )}
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
                  <span className="font-medium">
                    {deleteTarget.subject.name}
                  </span>
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

        {/* シラバス詳細モーダル */}
        {syllabusModalOpen && (
          <div
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              width: "100vw",
              height: "100vh",
              background: "rgba(0,0,0,0.5)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 1000,
            }}
            onClick={() => setSyllabusModalOpen(false)}
          >
            <div
              style={{
                background: "white",
                borderRadius: "8px",
                padding: "30px",
                maxWidth: "90vw",
                maxHeight: "90vh",
                overflow: "auto",
                position: "relative",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setSyllabusModalOpen(false)}
                style={{
                  position: "absolute",
                  top: 10,
                  right: 10,
                  background: "#1e3c72",
                  color: "white",
                  border: "none",
                  borderRadius: "50%",
                  width: "32px",
                  height: "32px",
                  fontSize: "18px",
                  cursor: "pointer",
                }}
              >
                ×
              </button>
              {syllabusModalLoading && (
                <div className="flex justify-center items-center py-8">
                  <div className="loading-spinner-small"></div>
                  <span className="ml-2 text-gray-500 text-sm">
                    シラバスを読み込み中...
                  </span>
                </div>
              )}
              {syllabusModalError && (
                <div style={{ color: "red" }}>{syllabusModalError}</div>
              )}
              {syllabusModalHtml && (
                <div
                  style={{
                    minWidth: "300px",
                    padding: "10px",
                    background: "#f9f9f9",
                    borderRadius: "8px",
                    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
                  }}
                >
                  <h2 style={{ color: "#1e3c72", marginTop: 0 }}>
                    シラバス詳細
                  </h2>
                  <hr style={{ margin: "10px 0 20px 0" }} />
                  <div
                    className="syllabus-html"
                    dangerouslySetInnerHTML={{ __html: syllabusModalHtml }}
                  />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
