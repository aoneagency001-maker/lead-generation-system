"use client";

/**
 * Competitor Parser Page
 * Страница парсинга сайтов конкурентов
 */

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { 
  Search, 
  Download, 
  AlertCircle, 
  CheckCircle, 
  Loader2,
  ExternalLink,
  TrendingUp
} from "lucide-react";

interface ParserTask {
  id: string;
  url: string;
  parser_type: string;
  status: string;
  progress: number;
  products_found: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

interface ParsedProduct {
  id: string;
  title: string;
  sku?: string;
  price_amount?: number;
  price_currency?: string;
  category?: string;
  brand?: string;
  source_url: string;
  source_site: string;
  parsed_at: string;
}

export default function ParserPage() {
  const [url, setUrl] = useState("");
  const [parserType, setParserType] = useState("universal");
  const [maxPages, setMaxPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [currentTask, setCurrentTask] = useState<ParserTask | null>(null);
  const [recentTasks, setRecentTasks] = useState<ParserTask[]>([]);
  const [products, setProducts] = useState<ParsedProduct[]>([]);
  const [stats, setStats] = useState({ total_tasks: 0, total_products: 0, total_sites: 0 });

  // Загрузка статистики
  useEffect(() => {
    loadStatistics();
    loadRecentTasks();
  }, []);

  // Polling задачи
  useEffect(() => {
    if (currentTask && (currentTask.status === "pending" || currentTask.status === "running")) {
      const interval = setInterval(() => {
        checkTaskStatus(currentTask.id);
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [currentTask]);

  const loadStatistics = async () => {
    try {
      const response = await fetch("/api/parser/statistics");
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error("Failed to load statistics:", error);
    }
  };

  const loadRecentTasks = async () => {
    try {
      const response = await fetch("/api/parser/tasks?limit=10");
      const data = await response.json();
      setRecentTasks(data);
    } catch (error) {
      console.error("Failed to load tasks:", error);
    }
  };

  const handleParse = async () => {
    if (!url) {
      alert("Введите URL");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/parser/parse", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url,
          parser_type: parserType,
          max_pages: maxPages,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to start parsing");
      }

      const data = await response.json();
      setCurrentTask({ ...data, id: data.task_id, url, parser_type: parserType, status: data.status, progress: 0, products_found: 0, created_at: new Date().toISOString() });
      
      // Начинаем проверку статуса
      checkTaskStatus(data.task_id);
    } catch (error) {
      console.error("Parse error:", error);
      alert("Ошибка при запуске парсинга");
    } finally {
      setLoading(false);
    }
  };

  const checkTaskStatus = async (taskId: string) => {
    try {
      const response = await fetch(`/api/parser/tasks/${taskId}`);
      const data = await response.json();
      setCurrentTask(data);

      // Если задача завершена, загружаем товары
      if (data.status === "completed") {
        loadTaskProducts(taskId);
        loadRecentTasks();
        loadStatistics();
      }
    } catch (error) {
      console.error("Failed to check task status:", error);
    }
  };

  const loadTaskProducts = async (taskId: string) => {
    try {
      const response = await fetch(`/api/parser/products?task_id=${taskId}`);
      const data = await response.json();
      setProducts(data);
    } catch (error) {
      console.error("Failed to load products:", error);
    }
  };

  const handleExport = async (format: string) => {
    if (!currentTask || !currentTask.id) {
      alert("Сначала запустите парсинг");
      return;
    }

    try {
      const response = await fetch(`/api/parser/export/${format}?task_id=${currentTask.id}`);
      
      if (!response.ok) {
        throw new Error("Export failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `export_${currentTask.id}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error("Export error:", error);
      alert("Ошибка при экспорте");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-500";
      case "running":
        return "bg-blue-500";
      case "failed":
        return "bg-red-500";
      default:
        return "bg-gray-500";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="h-4 w-4" />;
      case "running":
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case "failed":
        return <AlertCircle className="h-4 w-4" />;
      default:
        return <Loader2 className="h-4 w-4" />;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Парсер конкурентов</h1>
        <p className="text-muted-foreground">
          Парсинг товаров с сайтов конкурентов для анализа и создания ПБН
        </p>
      </div>

      {/* Statistics */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Всего задач</CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_tasks}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Товаров распарсено</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_products}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Сайтов</CardTitle>
            <ExternalLink className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_sites}</div>
          </CardContent>
        </Card>
      </div>

      {/* Parse Form */}
      <Card>
        <CardHeader>
          <CardTitle>Запустить парсинг</CardTitle>
          <CardDescription>
            Введите URL товара или категории для парсинга
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="url">URL</Label>
              <Input
                id="url"
                placeholder="https://satu.kz/..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
              />
            </div>
            
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="parser-type">Тип парсера</Label>
                <Select value={parserType} onValueChange={setParserType}>
                  <SelectTrigger id="parser-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="universal">Универсальный</SelectItem>
                    <SelectItem value="satu">Satu.kz</SelectItem>
                    <SelectItem value="kaspi">Kaspi.kz</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="max-pages">Макс. страниц</Label>
                <Input
                  id="max-pages"
                  type="number"
                  min="1"
                  max="10"
                  value={maxPages}
                  onChange={(e) => setMaxPages(parseInt(e.target.value) || 1)}
                />
              </div>
            </div>

            <Button
              onClick={handleParse}
              disabled={loading || !url}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Запуск...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Запустить парсинг
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Current Task Status */}
      {currentTask && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {getStatusIcon(currentTask.status)}
              Статус задачи
            </CardTitle>
            <CardDescription>{currentTask.url}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <Badge className={getStatusColor(currentTask.status)}>
                {currentTask.status}
              </Badge>
              <span className="text-sm text-muted-foreground">
                Найдено товаров: {currentTask.products_found}
              </span>
            </div>

            {currentTask.progress > 0 && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Прогресс</span>
                  <span>{currentTask.progress}%</span>
                </div>
                <Progress value={currentTask.progress} />
              </div>
            )}

            {currentTask.error_message && (
              <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-800">
                <AlertCircle className="inline h-4 w-4 mr-2" />
                {currentTask.error_message}
              </div>
            )}

            {currentTask.status === "completed" && (
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleExport("json")}>
                  <Download className="mr-2 h-4 w-4" />
                  JSON
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleExport("csv")}>
                  <Download className="mr-2 h-4 w-4" />
                  CSV
                </Button>
                <Button variant="outline" size="sm" onClick={() => handleExport("wordpress_xml")}>
                  <Download className="mr-2 h-4 w-4" />
                  WordPress XML
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results */}
      <Tabs defaultValue="products" className="space-y-4">
        <TabsList>
          <TabsTrigger value="products">Товары ({products.length})</TabsTrigger>
          <TabsTrigger value="tasks">История задач ({recentTasks.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="products" className="space-y-4">
          {products.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Распарсенные товары</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Название</TableHead>
                      <TableHead>SKU</TableHead>
                      <TableHead>Цена</TableHead>
                      <TableHead>Категория</TableHead>
                      <TableHead>Бренд</TableHead>
                      <TableHead>Сайт</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {products.map((product) => (
                      <TableRow key={product.id}>
                        <TableCell className="font-medium">
                          <a
                            href={product.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline flex items-center gap-1"
                          >
                            {product.title}
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        </TableCell>
                        <TableCell>{product.sku || "-"}</TableCell>
                        <TableCell>
                          {product.price_amount
                            ? `${product.price_amount} ${product.price_currency || "KZT"}`
                            : "-"}
                        </TableCell>
                        <TableCell>{product.category || "-"}</TableCell>
                        <TableCell>{product.brand || "-"}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{product.source_site}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                Нет распарсенных товаров. Запустите парсинг.
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="tasks" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>История парсинга</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>URL</TableHead>
                    <TableHead>Тип</TableHead>
                    <TableHead>Статус</TableHead>
                    <TableHead>Товаров</TableHead>
                    <TableHead>Дата</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentTasks.map((task) => (
                    <TableRow key={task.id}>
                      <TableCell className="max-w-xs truncate">{task.url}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{task.parser_type}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusColor(task.status)}>
                          {task.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{task.products_found}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(task.created_at).toLocaleString("ru-RU")}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}


