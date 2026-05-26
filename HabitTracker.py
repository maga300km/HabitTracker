import csv
import json
import io
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from fastapi import FastAPI, UploadFile


class HabitTracker:

    def __init__(self, csvfile):
        self.habits = []
        self.csvfile = csvfile
        self.df = pd.DataFrame()
        self._load_csv(csvfile)
        self._refresh_df()

    def _load_csv(self, csvfile):
        with open(csvfile, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row['done'] = int(row['done'])
                self.habits.append(row)

    def _refresh_df(self):
        self.df = pd.DataFrame(self.habits)

    def add_habit(self, user, habit, date, done):
        if user.strip() == "" or habit.strip() == "" or date.strip() == "":
            print("Барлық жолдарды толтырыңыз")
            return
        try:
            datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            print("Қате: күн форматы YYYY-MM-DD болу керек")
            return
        if done not in [0, 1]:
            print("Done 1 немесе 0 болу керек")
            return
        record = {'user': user, 'habit': habit, 'date': date, 'done': done}
        self.habits.append(record)
        self._refresh_df()
        print(f"Әдет қосылды: {record}")

    def show_habits(self):
        for r in self.habits:
            print(f"Пайдаланушы: {r['user']} | Әдет: {r['habit']} | Күні: {r['date']} | Орындалды: {r['done']}")

    def find_by_user(self, user):
        return [x for x in self.habits if x['user'] == user]

    def find_by_habit(self, habit):
        return [x for x in self.habits if x['habit'] == habit]

    def find_by_date(self, date):
        return [x for x in self.habits if x['date'] == date]

    def user_records(self, user):
        for record in self.habits:
            if record['user'] == user:
                yield record

    def export_json(self, filename='output/habits.json'):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.habits, f, ensure_ascii=False, indent=2)

    def export_csv(self, filename='output/habits_export.csv'):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['user', 'habit', 'date', 'done'])
            writer.writeheader()
            writer.writerows(self.habits)

    def completion_rate(self):
        done_array = np.array([x['done'] for x in self.habits])
        rate = float(np.mean(done_array) * 100)
        print(f"Жалпы орындалу пайызы: {rate:.1f}%")
        return rate

    def completion_by_user(self):
        unique_users = list({x['user'] for x in self.habits})
        for user in unique_users:
            user_done = np.array([x['done'] for x in self.habits if x['user'] == user])
            print(f"{user}: {np.mean(user_done) * 100:.1f}%")

    def describe(self):
        return self.df.describe()

    def groupby_habit(self, output_csv='output/summary_habits.csv'):
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        summary = self.df.groupby('habit')['done'].agg(['mean', 'count'])
        summary.columns = ['completion_rate', 'total']
        summary['completion_rate'] = (summary['completion_rate'] * 100).round(2)
        summary.to_csv(output_csv)
        return summary

    def plot_progress(self, output_png='output/progress.png'):
        os.makedirs(os.path.dirname(output_png), exist_ok=True)
        summary = self.df.groupby('habit')['done'].mean() * 100
        plt.figure(figsize=(10, 6))
        plt.bar(summary.index, summary.values, color='steelblue')
        plt.xlabel('Әдет')
        plt.ylabel('Орындалу %')
        plt.title('Әдеттердің орындалу пайызы')
        plt.tight_layout()
        plt.savefig(output_png)
        plt.close()

    def run(self):
        user = input("Пайдаланушы аты: ")
        habit = input("Әдет: ")
        date = input("Күні (YYYY-MM-DD): ")
        done = int(input("Орындалды? (1/0): "))
        self.add_habit(user, habit, date, done)

        name = input("Пайдаланушыны іздеу: ")
        print(self.find_by_user(name))

        habit_s = input("Әдет бойынша іздеу: ")
        print(self.find_by_habit(habit_s))

        date_s = input("Күні бойынша іздеу (YYYY-MM-DD): ")
        print(self.find_by_date(date_s))

        for rec in self.user_records(name):
            print(rec)

        self.export_json()
        self.export_csv()

        self.completion_rate()
        self.completion_by_user()

        print(self.describe())
        print(self.groupby_habit())

        self.plot_progress()
        self.show_habits()


app = FastAPI()

@app.post("/report")
async def report(file: UploadFile):
    content = await file.read()
    df = pd.read_csv(io.StringIO(content.decode('utf-8')))
    completion = df.groupby('habit')['done'].mean() * 100
    return {
        "global_completion": round(float(df['done'].mean() * 100), 2),
        "by_habit": completion.round(2).to_dict()
    }


if __name__ == '__main__':
    tracker = HabitTracker('data/data.csv')
    tracker.run()