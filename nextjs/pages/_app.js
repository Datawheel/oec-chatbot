import {MantineProvider} from "@mantine/core";
import {DefaultSeo} from "next-seo";

export default function App(props) {
  const {Component, pageProps} = props;

  return (
    <>
      <DefaultSeo title="DataUSA Chat" titleTemplate="%s | DataUSA Chat" />
      <MantineProvider
        withGlobalStyles
        withNormalizeCSS
        theme={{
          /** Put your mantine theme override here */
          colorScheme: "dark",
        }}
      >
        <Component {...pageProps} />
      </MantineProvider>
    </>
  );
}
