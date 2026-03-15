import React, { useMemo, useState } from 'react';
import { SafeAreaView, View, Text, TextInput, Pressable, ScrollView, StyleSheet, Platform } from 'react-native';
import { StatusBar } from 'expo-status-bar';

const API_BASE = Platform.select({
  web: 'http://127.0.0.1:5000',
  default: 'http://10.0.2.2:5000'
});

const Section = ({ title, children }) => (
  <View style={styles.card}>
    <Text style={styles.title}>{title}</Text>
    {children}
  </View>
);

export default function App() {
  const [email, setEmail] = useState('');
  const [nickname, setNickname] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [heartRate, setHeartRate] = useState('72');
  const [dashboard, setDashboard] = useState(null);
  const [msg, setMsg] = useState('');

  const canCall = useMemo(() => email.trim().length > 5, [email]);

  const post = async (path, body) => {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || '请求失败');
    }
    return data;
  };

  const get = async (path) => {
    const res = await fetch(`${API_BASE}${path}`);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || '请求失败');
    }
    return data;
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.header}>GuardianMe（守护么）</Text>
        <Text style={styles.subHeader}>一套代码支持 Web / iOS / Android 的安全守护应用 MVP</Text>

        <Section title="1) 注册用户">
          <TextInput style={styles.input} placeholder="邮箱" value={email} onChangeText={setEmail} autoCapitalize="none" />
          <TextInput style={styles.input} placeholder="昵称" value={nickname} onChangeText={setNickname} />
          <Pressable
            style={styles.button}
            onPress={async () => {
              try {
                const data = await post('/api/register', { email, nickname });
                setMsg(`注册成功：${data.nickname}`);
              } catch (e) {
                setMsg(e.message);
              }
            }}
          >
            <Text style={styles.buttonText}>注册</Text>
          </Pressable>
        </Section>

        <Section title="2) 每日签到">
          <Pressable
            style={[styles.button, !canCall && styles.disabled]}
            disabled={!canCall}
            onPress={async () => {
              try {
                const data = await post('/api/checkin', { email });
                setMsg(`签到成功：${data.last_checkin_at}`);
              } catch (e) {
                setMsg(e.message);
              }
            }}
          >
            <Text style={styles.buttonText}>我今天平安</Text>
          </Pressable>
        </Section>

        <Section title="3) 紧急联系人">
          <TextInput style={styles.input} placeholder="联系人姓名" value={contactName} onChangeText={setContactName} />
          <TextInput style={styles.input} placeholder="联系人手机号" value={contactPhone} onChangeText={setContactPhone} />
          <Pressable
            style={[styles.button, !canCall && styles.disabled]}
            disabled={!canCall}
            onPress={async () => {
              try {
                await post('/api/contacts', {
                  email,
                  name: contactName,
                  phone: contactPhone,
                  channel_priority: 'email,sms,whatsapp'
                });
                setMsg('联系人添加成功');
              } catch (e) {
                setMsg(e.message);
              }
            }}
          >
            <Text style={styles.buttonText}>添加联系人</Text>
          </Pressable>
        </Section>

        <Section title="4) 生命体征上报">
          <TextInput style={styles.input} placeholder="心率 (bpm)" value={heartRate} onChangeText={setHeartRate} keyboardType="numeric" />
          <Pressable
            style={[styles.button, !canCall && styles.disabled]}
            disabled={!canCall}
            onPress={async () => {
              try {
                const data = await post('/api/vitals', { email, heart_rate: Number(heartRate) });
                setMsg(data.alert ? `已触发告警：${data.alert}` : '生命体征记录成功');
              } catch (e) {
                setMsg(e.message);
              }
            }}
          >
            <Text style={styles.buttonText}>提交心率</Text>
          </Pressable>
        </Section>

        <Section title="5) 家属看板">
          <Pressable
            style={[styles.button, !canCall && styles.disabled]}
            disabled={!canCall}
            onPress={async () => {
              try {
                const data = await get(`/api/dashboard/${email}`);
                setDashboard(data);
                setMsg('看板已刷新');
              } catch (e) {
                setMsg(e.message);
              }
            }}
          >
            <Text style={styles.buttonText}>刷新状态</Text>
          </Pressable>

          {dashboard && (
            <View style={styles.dashboardBox}>
              <Text>用户：{dashboard.user.nickname} ({dashboard.user.email})</Text>
              <Text>最后签到：{dashboard.user.last_checkin_at || '暂无'}</Text>
              <Text>最新心率：{dashboard.latest_vital?.heart_rate ?? '暂无'}</Text>
              <Text>最近通知数：{dashboard.recent_notifications?.length ?? 0}</Text>
            </View>
          )}
        </Section>

        <Text style={styles.message}>{msg}</Text>
      </ScrollView>
      <StatusBar style="auto" />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f3f4f6' },
  content: { padding: 16, gap: 12 },
  header: { fontSize: 24, fontWeight: '700', color: '#111827' },
  subHeader: { color: '#4b5563', marginBottom: 4 },
  card: { backgroundColor: 'white', borderRadius: 12, padding: 12, gap: 8 },
  title: { fontWeight: '700', fontSize: 16 },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 10,
    paddingHorizontal: 10,
    paddingVertical: 8,
    backgroundColor: 'white'
  },
  button: {
    backgroundColor: '#2563eb',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center'
  },
  disabled: { opacity: 0.5 },
  buttonText: { color: 'white', fontWeight: '700' },
  dashboardBox: { backgroundColor: '#eef2ff', padding: 10, borderRadius: 8, gap: 4 },
  message: { color: '#065f46', fontWeight: '600', marginVertical: 8 }
});
